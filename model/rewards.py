from abc import ABCMeta, abstractmethod

from .skills import Skills
from .skillset import SkillSet


class XpReward(metaclass=ABCMeta):
    def __init__(self, quest_id: int, amount: int, skills: Skills):
        self.quest_id = quest_id
        self.amount = amount
        self.skills = skills

    def __lt__(self, other):
        if isinstance(other, XpReward):
            return self.amount < other.amount
        return NotImplemented

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
        elif data['type'] == 'Claimable':
            return ClaimableXpReward(
                quest_id=quest_id,
                amount=data['amount'],
                skill=XpReward.parse_skills(data['skills']),
                minimum_level=data.get('minimum_level', 1),
                source=data['source']
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
    def get_reward(self, **kwargs):
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

    def get_reward(self, skill_choice: Skills):
        if skill_choice not in self.skills:
            raise ValueError
        return SkillSet({skill_choice: self.amount})

    def is_claimable(self, player_skills: SkillSet, skill: Skills):
        if skill in self.skills:
            return self.minimum_xp <= player_skills[skill]
        return False

    def __str__(self):
        return f'{self.amount} xp reward'


class ClaimableXpReward(ImmediateXpReward):
    def __init__(self, quest_id: int, amount: int, skill: Skills, minimum_level: int, source: str):
        super(ClaimableXpReward, self).__init__(quest_id, amount, skill)
        self.claim_source = source
        self.minimum_xp = Skills.min_xp_for_level(minimum_level)

    def is_claimable(self, player_skills: SkillSet, *args, **kwargs):
        return self.minimum_xp <= player_skills[self.skills]

    def __str__(self):
        return f'{self.amount} {self.skills} xp from {self.claim_source} (quest {self.quest_id})'


class ClaimableChoiceXpReward(ChoiceXpReward):
    def __init__(self, quest_id: int, amount: int, skills: Skills, minimum_level: int, source: str):
        super(ClaimableChoiceXpReward, self).__init__(quest_id, amount, skills, minimum_level)
        self.claim_source = source

    def __str__(self):
        return f'{self.amount} xp reward from {self.claim_source} (quest {self.quest_id})'
