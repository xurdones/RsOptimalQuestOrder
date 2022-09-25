from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from math import floor

from .skills import Skills
from .skillset import SkillSet


class XpReward(metaclass=ABCMeta):
    def __init__(self, quest_id: int, amount: int, skills: Skills):
        self.quest_id = quest_id
        self._amount = amount
        self.skills = skills

    def __lt__(self, other):
        if isinstance(other, PrismaticXpReward):
            return True
        elif isinstance(other, XpReward):
            return self.amount() < other.amount()
        return NotImplemented

    def amount(self, *args, **kwargs):
        return self._amount

    def is_claimable(self, player_skills: SkillSet, skill: Skills) -> bool:
        return True

    @staticmethod
    def from_json(data, quest_id: int) -> 'XpReward':
        if data['type'] == 'Immediate':
            return ImmediateXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skill=XpReward.parse_skills(data['skills']),
            )
        elif data['type'] == 'Choice':
            return ChoiceXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skills=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1)
            )
        elif data['type'] == 'ClaimableChoice':
            return ClaimableChoiceXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skills=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1),
                source=data['source']
            )
        elif data['type'] == 'Tiered':
            return ClaimableChoiceXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skills=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1),
                source=data['source']
            )
        elif data['type'] == 'Claimable':
            return ClaimableXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skill=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1),
                source=data['source']
            )
        elif data['type'] == 'Prismatic':
            return PrismaticXpReward(
                quest_id=quest_id,
                size=PrismaticXpReward.PrismaticSize[data['size'].upper()],
                skills=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1),
            )
        raise NotImplementedError

    @staticmethod
    def parse_skills(skills_str: str) -> Skills:
        res = Skills.NONE
        tokens = skills_str.split(',')

        for token in tokens:
            res |= Skills[token.upper()]

        return res

    @abstractmethod
    def get_reward(self, *args, **kwargs):
        raise NotImplementedError


class ImmediateXpReward(XpReward):
    def __init__(self, quest_id: int, amount: int, skill: Skills):
        super(ImmediateXpReward, self).__init__(quest_id, amount, skill)
        self._reward = SkillSet({skill: amount})

    def get_reward(self, *args, **kwargs):
        return self._reward

    def is_claimable(self, player_skills: SkillSet, *args, **kwargs):
        return True


class ChoiceXpReward(XpReward):
    def __init__(self, quest_id: int, amount: int, skills: Skills, minimum_level: int):
        super(ChoiceXpReward, self).__init__(quest_id, amount, skills)
        self.minimum_xp = Skills.min_xp_for_level(minimum_level)

    def get_reward(self, skill_choice: Skills, *args, **kwargs):
        if skill_choice not in self.skills:
            raise ValueError
        return SkillSet({skill_choice: self.amount()})

    def is_claimable(self, player_skills: SkillSet, skill: Skills):
        if skill in self.skills:
            return self.minimum_xp <= player_skills[skill]
        return False

    def __str__(self):
        return f'{self.amount()} xp reward'


class ClaimableXpReward(ImmediateXpReward):
    def __init__(self, quest_id: int, amount: int, skill: Skills, minimum_level: int, source: str):
        super(ClaimableXpReward, self).__init__(quest_id, amount, skill)
        self.claim_source = source
        self.minimum_xp = Skills.min_xp_for_level(minimum_level)

    def is_claimable(self, player_skills: SkillSet, *args, **kwargs):
        return self.minimum_xp <= player_skills[self.skills]

    def __str__(self):
        return f'Claim {self.amount()} {self.skills} xp from {self.claim_source} (quest {self.quest_id})'


class ClaimableChoiceXpReward(ChoiceXpReward):
    def __init__(self, quest_id: int, amount: int, skills: Skills, minimum_level: int, source: str):
        super(ClaimableChoiceXpReward, self).__init__(quest_id, amount, skills, minimum_level)
        self.claim_source = source

    def __str__(self):
        return f'{self.amount()} xp reward from {self.claim_source} (quest {self.quest_id})'


class TieredXpReward(ClaimableChoiceXpReward):
    def __init__(self, quest_id: int, amount: int, skills: Skills, minimum_level: int, source: str):
        super(TieredXpReward, self).__init__(quest_id, amount, skills, minimum_level=0, source=source)
        self.tier_requirement = Skills.min_xp_for_level(minimum_level)

    def is_claimable(self, player_skills: SkillSet, *args, **kwargs):
        return all(p_skill >= self.tier_requirement for p_skill, p_value in player_skills if p_skill in self.skills)


class PrismaticXpReward(ChoiceXpReward):
    class PrismaticSize(Enum):
        SMALL = 1
        MEDIUM = 2
        LARGE = 3
        HUGE = 4

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented

        def __str__(self):
            return self.name.capitalize()

    PRISMATIC_REWARDS = {
        PrismaticSize.SMALL: lambda l: floor(-3E-6*l**5 + 6E-4*l**4 - 2.8E-2*l**3 + 0.5823*l**2+ 9.3594*l + 45.49),
        PrismaticSize.MEDIUM: lambda l: floor(-5E-6*l**5 + 1.1E-3*l**4 - 0.0559*l**3 + 1.1645*l**2 + 18.719*l + 90.981),
        PrismaticSize.LARGE: lambda l: floor(-1E-5*l**5 + 2.3E-3*l**4 - 0.1118*l**3 + 2.329*l**2 + 37.437*l + 181.96),
        PrismaticSize.HUGE: lambda l: floor(-2E-5*l**5 + 4.6E-3*l**4 - 0.2237*l**3 + 4.6581*l**2 + 74.875*l + 363.92)
    }

    def __init__(self, quest_id: int, size: PrismaticSize, skills: Skills, minimum_level: int):
        super(PrismaticXpReward, self).__init__(quest_id=quest_id, amount=0, skills=skills, minimum_level=minimum_level)
        self.size = size

    def __lt__(self, other):
        if isinstance(other, PrismaticXpReward):
            return self.size < other.size
        elif isinstance(other, XpReward):
            return False
        return NotImplemented

    def get_reward(self, skill_choice: Skills, player_skills: SkillSet):
        return SkillSet({skill_choice: self.amount(player_skills, skill_choice)})

    def amount(self, player_skills: SkillSet, skill_choice: Skills, *args, **kwargs):
        return self.PRISMATIC_REWARDS[self.size](Skills.level_for_xp(player_skills[skill_choice]))

    def __str__(self):
        return f'{self.size} xp lamp'


class ClaimedChoiceXpReward:
    def __init__(self, reward: XpReward, skill_choice: Skills):
        self.reward = reward
        self.skill_choice = skill_choice

    def __str__(self):
        return f'Use {self.reward} on {self.skill_choice}'