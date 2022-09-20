from math import floor

from .rewards import XpReward, ImmediateXpReward, ClaimableXpReward
from .skills import Skills
from .skillset import SkillSet


class Player:
    def __init__(self, initial_stats: SkillSet = None):
        initial_stats = initial_stats or SkillSet()
        self.skills = initial_stats
        self.quest_points = 1
        self.quests_completed = set()
        self._explicit_combat_level = 1

    @property
    def combat_level(self) -> int:
        return max(self._explicit_combat_level, Skills.calculate_combat_level({
            Skills.ATTACK: Skills.level_for_xp(self.skills[Skills.ATTACK]),
            Skills.STRENGTH: Skills.level_for_xp(self.skills[Skills.STRENGTH]),
            Skills.DEFENCE: Skills.level_for_xp(self.skills[Skills.DEFENCE]),
            Skills.RANGED: Skills.level_for_xp(self.skills[Skills.RANGED]),
            Skills.MAGIC: Skills.level_for_xp(self.skills[Skills.MAGIC]),
            Skills.CONSTITUTION: Skills.level_for_xp(self.skills[Skills.CONSTITUTION]),
            Skills.PRAYER: Skills.level_for_xp(self.skills[Skills.PRAYER]),
            Skills.SUMMONING: Skills.level_for_xp(self.skills[Skills.SUMMONING]),
        }))

    def complete_quest(self, quest: int, quest_points: int, rewards: [XpReward]) -> ([XpReward], set[XpReward]):
        self.quests_completed.add(quest)
        self.quest_points += quest_points

        claimed_rewards = []
        hoarded_rewards = set()
        for reward in rewards:
            if isinstance(reward, ClaimableXpReward) and reward.is_claimable(self.skills):
                claimed_rewards.append(reward)
            if isinstance(reward, ImmediateXpReward) and reward.is_claimable(self.skills):
                self.skills += reward.get_reward()
            else:
                hoarded_rewards.add(reward)
        return claimed_rewards, hoarded_rewards

    def set_combat_level(self, value: int):
        self._explicit_combat_level = value

