from enum import Enum

from .player import Player
from .skillset import SkillSet
from .rewards import XpReward

__all__ = ['Quest', 'Difficulty']


class OrderedEnum(Enum):
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __ge__(self, other):
        return self > other or self == other

    def __gt__(self, other):
        return not self < other

    def __le__(self, other):
        return self < other or self == other


class Difficulty(OrderedEnum):
    NOVICE = 1
    INTERMEDIATE = 2
    EXPERIENCED = 3
    MASTER = 4
    GRANDMASTER = 5
    SPECIAL = 6


class Quest:
    def __init__(self, id: int, name: str, difficulty: Difficulty, combat_requirement: int, qp_requirement: int,
                 quest_reqs: [int], skill_reqs: SkillSet, quest_points: int, rewards: [XpReward]):
        self.id: int = id
        self.name: str = name
        self.difficulty = difficulty

        self.qp_requirement = qp_requirement
        self.combat_requirement = combat_requirement
        self.combat_training_requirement = SkillSet.optimal_route_to_combat_level(combat_requirement)
        self.quest_prereqs = set(quest_reqs)
        self.skill_prereqs = skill_reqs

        self.quest_points: int = quest_points
        self.xp_rewards = rewards

    def __lt__(self, other):
        if not isinstance(other, Quest):
            return False
        return (self.difficulty, self.skill_prereqs + self.combat_training_requirement) \
               < (other.difficulty, other.skill_prereqs+ other.combat_training_requirement)

    def satisfies_requirements(self, player: Player):
        return all([
            self.skill_prereqs <= player.skills,
            self.combat_requirement <= player.combat_level,
            self.qp_requirement <= player.quest_points,
            self.quest_prereqs <= player.quests_completed
        ])
