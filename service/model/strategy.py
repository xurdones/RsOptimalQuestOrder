from service.model import XpReward
from service.model.quest import Quest
from service.util import MyOrderedDict

__all__ = ['QuestStrategy']


class StrategyItem:
    def __init__(self, quest: Quest, rewards: [XpReward]):
        self.quest = quest
        self.rewards = rewards

    def add_reward(self, reward: XpReward):
        self.rewards.append(reward)

    def push_reward(self, reward: XpReward):
        self.rewards.insert(0, reward)


class QuestStrategy:
    def __init__(self):
        self.strategy: MyOrderedDict[int, StrategyItem] = MyOrderedDict()

    def add_reward(self, reward: XpReward, quest_id: int = None):
        self.add_rewards([reward], quest_id)

    def add_rewards(self, rewards: [XpReward], quest_id: int = None):
        quest_id = quest_id or self.strategy.last()
        for reward in rewards:
            self.strategy[quest_id].add_reward(reward)

    def push_reward(self, reward: XpReward, quest_id: int = None):
        quest_id = quest_id or self.strategy.last()
        self.strategy[quest_id].push_reward(reward)

    def add_quest(self, quest: Quest, rewards: [XpReward]):
        self.strategy[quest.id] = StrategyItem(quest, rewards)

    def __iter__(self):
        return iter(self.strategy)

    def __getitem__(self, item):
        return self.strategy[item]
