import json
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from .model import Player, SkillSet, Skills
from .model.quest import Quest, Difficulty
from .model.rewards import XpReward, ClaimableXpReward, ChoiceXpReward, ClaimableChoiceXpReward, ClaimedChoiceXpReward
from .model.strategy import QuestStrategy
from .util import partition

__all__ = ['get_optimal_quest_strategy']


def load_quest_data(filename) -> dict[int, Quest]:
    quest_list = {}
    with open(filename) as f:
        data = json.load(f)

    for quest in data:
        if quest["id"] in quest_list:
            raise ValueError
        quest_list[quest["id"]] = Quest(id=quest["id"], name=quest["name"], difficulty=Difficulty[quest["difficulty"].upper()],
                                        combat_requirement=quest.get("combat_requirement", 0),
                                        qp_requirement=quest.get("qp_requirement", 0),
                                        quest_reqs=quest.get("quest_requirements", []),
                                        skill_reqs=SkillSet.from_json(quest.get("skill_requirements", [])),
                                        quest_points=quest.get("quest_points", 0),
                                        rewards=[XpReward.from_json(reward, quest["id"]) for reward in quest.get("xp_rewards", [])])
    return quest_list


def choose_next_quest(shell: [int], player: Player, quest_list: [Quest]) -> Optional[int]:
    for idx, quest_id in enumerate(shell):
        if quest_list[quest_id].satisfies_requirements(player):
            return idx
    return None


def build_quest_postreqs(quests: [Quest]) -> dict[int, [int]]:
    res = {}

    for quest_id, quest in quests.items():
        for prereq_id in quest.quest_prereqs:
            if prereq_id not in res:
                res[prereq_id] = []
            res[prereq_id].append(quest_id)

    return res


# noinspection PyShadowingNames
def get_next_lamp(player_skills: SkillSet, xp_gap: SkillSet, skill: Skills, rewards: set[XpReward]) -> Optional[XpReward]:
    options = sorted(reward for reward in rewards if reward.is_claimable(player_skills, skill))
    if not options:
        return None
    return min(options, key=lambda r: abs(r.amount(player_skills, skill) - xp_gap[skill]))


# noinspection PyShadowingNames
def optimal_search(player: Player, quest_list: dict[int, Quest]) -> QuestStrategy:
    strategy = QuestStrategy()

    # Set of all quests with no incoming edges, i.e. we satisfy all quest pre-reqs
    # Sorted by the quest ordering, which sorts on (skill requirements, combat requirement, difficulty)
    shell = [q for q in quest_list if not quest_list[q].quest_prereqs]

    postreq_relation = build_quest_postreqs(quest_list)
    hoarded_rewards = set()

    # This is Kahn's algorithm, with a twist at the end
    # https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm
    while shell:

        # First of, low-hanging fruit: check all of our Claimable rewards to see if we meet the requirements
        # If yes, claim them and remove from the hoard
        to_hoard, to_claim = partition(
            lambda r: isinstance(r, ClaimableXpReward) and r.is_claimable(player.skills),
            hoarded_rewards
        )

        for reward in to_claim:
            player.skills += reward.get_reward()
            strategy.add_reward(reward)

        hoarded_rewards = set(to_hoard)

        shell.sort(key=lambda q: quest_list[q])
        # Get the next quest we can complete; the first quest in the shell we satisfy all requirements for
        idx = choose_next_quest(shell, player, quest_list)
        if idx is not None:
            next_quest = quest_list[shell.pop(idx)]
            claimed_rewards, unclaimed_rewards = player.complete_quest(
                next_quest.id,
                next_quest.quest_points,
                next_quest.xp_rewards
            )
            strategy.add_quest(next_quest, claimed_rewards)
            hoarded_rewards.update(unclaimed_rewards)

            # We're looking for every quest that has this one as a prereq
            postreq_ids = postreq_relation.pop(next_quest.id, [])
            for pr_id in postreq_ids:
                # If we've completed all of its prereqs, the quest is a candidate for the next iteration
                if quest_list[pr_id].quest_prereqs <= player.quests_completed:
                    shell.append(pr_id)
        else:
            # This is where we diverge from Kahn's algorithm
            # At this point we have to do some work, either use an unclaimed/unchosen reward, or do some training
            # We're going to prioritise claiming rewards over training, because our goal is to minimize training

            # We don't need to re-check the Claimables, because we haven't completed a quest since the last iteration
            # The basic idea is this: we iterate over the quests in the shell
            # For each quest, we calculate the training delta (skill_prereqs - player.skills), and apply lamps to
            #   lower that delta, until either we run out or the delta is negative
            prospects: {int, (SkillSet, [(XpReward, Skills)])} = {}
            for quest_id in shell:
                hoarded_rewards_copy: set[XpReward] = hoarded_rewards.copy()
                player_skills_copy = player.skills.copy()
                quest = quest_list[quest_id]
                xp_gap = quest.skill_prereqs + quest.combat_training_requirement - player.skills
                loop_flag = True

                prospects[quest_id] = (xp_gap, [])

                while +xp_gap and hoarded_rewards_copy and loop_flag:
                    for (skill, required_xp) in (+xp_gap).most_common():
                        # Want to get the lamp that is:
                        #   1) in absolute terms closest to filling the xp gap
                        #   2) is claimable at our stats
                        while next_lamp := get_next_lamp(player_skills_copy, xp_gap, skill, hoarded_rewards_copy):
                            loop_flag = True
                            hoarded_rewards_copy.remove(next_lamp)
                            reward = next_lamp.get_reward(skill_choice=skill, player_skills=player_skills_copy)
                            xp_gap.subtract(reward)
                            player_skills_copy += reward
                            prospects[quest_id][1].append(ClaimedChoiceXpReward(next_lamp, skill))
                        loop_flag = False

            # At this point we take the option closest to zero
            choice = min(prospects, key=lambda p: prospects[p][0])
            for reward in prospects[choice][1]:
                hoarded_rewards.remove(reward.reward)
                player.skills += reward.reward.get_reward(reward.skill_choice, player.skills)

                if isinstance(reward.reward, ClaimableXpReward) or isinstance(reward.reward, ClaimableChoiceXpReward):
                    strategy.add_reward(reward)
                elif isinstance(reward.reward, ChoiceXpReward):
                    strategy.push_reward(reward, reward.reward.quest_id)

            training_goal = quest_list[choice].skill_prereqs - player.skills
            if training_goal:
                player.skills += training_goal
                strategy.add_rewards([f'Train {skill} to level {Skills.level_for_xp(quest_list[choice].skill_prereqs[skill])} (+{training_goal[skill]} xp)' for skill in training_goal])

            if player.combat_level < quest_list[choice].combat_requirement:
                combat_training_strategy = SkillSet.optimal_route_to_combat_level(
                    quest_list[choice].combat_requirement,
                    player.skills
                )
                player.skills += combat_training_strategy
                for skill, xp in combat_training_strategy.items():
                    strategy.add_reward(f'Train {skill} to level {Skills.level_for_xp(player.skills[skill])} (+{xp} xp)')
    return strategy


def get_optimal_quest_strategy():
    data_file = Path(__file__).resolve().parent / 'quest_data.json'
    quests = load_quest_data(data_file)

    player = Player()
    strategy = optimal_search(player, quests)

    return strategy
