from collections import Counter
from enum import unique, Flag
from functools import reduce
from math import floor, ceil
from operator import or_ as _or_

__all__ = ['Skills']


# https://stackoverflow.com/a/42253518/3457753
# noinspection PyProtectedMember
def with_limits(enumeration):
    none_mbr = enumeration(0)
    all_mbr = enumeration(reduce(_or_, enumeration))
    enumeration._member_map_['NONE'] = none_mbr
    enumeration._member_map_['ALL'] = all_mbr
    return enumeration


XP_TABLE = [-1, 0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973,
            4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406,
            24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333,
            111945, 123660, 136594, 150872, 166636, 184040, 203254, 224466, 247866, 273742, 302288, 333804, 368599,
            407015, 449428, 496254, 547953, 605032, 668051, 737627, 814445, 899257, 992895, 1096278, 1210421, 1336443,
            1475581, 1629200, 1798808, 1986068, 2192818, 2421087, 2673114, 2951373, 3258594, 3597792, 3972294, 4385776,
            4842295, 5346332, 5902831, 6517253, 7195629, 7944614, 8771558, 9684577, 10692629, 11805606, 13034431,
            14391160, 15889109, 17542976, 19368992, 21385073, 23611006, 26068632, 26782069, 31777943, 35085654,
            38737661, 42769801, 47221641, 52136869, 57563718, 63555443, 70170840, 77474828, 85539082, 94442737,
            104273167]


@with_limits
@unique
class Skills(Flag):

    def __new__(cls, value, initial_level=1):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.initial = cls.min_xp_for_level(initial_level)
        return obj

    @staticmethod
    def min_xp_for_level(level: int) -> int:
        if level < 1:
            raise ValueError(f'Level must be greater than 0, found {level}')
        elif level > 120:
            raise ValueError(f'Level cannot be greater than 1200, found {level}')
        return XP_TABLE[level]

    @staticmethod
    def level_for_xp(xp: int) -> int:
        if xp < 0:
            raise ValueError(f'Experience cannot be negative, found {xp}')
        for idx, max_xp in enumerate(XP_TABLE, start=1):
            if xp <= max_xp:
                return idx - 1
        return 120

    ATTACK = 2 ** 0
    STRENGTH = 2 ** 1
    DEFENCE = 2 ** 2
    RANGED = 2 ** 3
    PRAYER = 2 ** 4
    MAGIC = 2 ** 5
    CONSTITUTION = 2 ** 6, 10
    CRAFTING = 2 ** 7
    MINING = 2 ** 8
    SMITHING = 2 ** 9
    FISHING = 2 ** 10
    COOKING = 2 ** 11
    FIREMAKING = 2 ** 12
    WOODCUTTING = 2 ** 13
    RUNECRAFTING = 2 ** 14
    DUNGEONEERING = 2 ** 15
    FLETCHING = 2 ** 16
    AGILITY = 2 ** 17
    HERBLORE = 2 ** 18
    THIEVING = 2 ** 19
    SLAYER = 2 ** 20
    FARMING = 2 ** 21
    CONSTRUCTION = 2 ** 22
    HUNTER = 2 ** 23
    SUMMONING = 2 ** 24
    DIVINATION = 2 ** 25
    ARCHAEOLOGY = 2 ** 26

    def __str__(self):
        return self.name.capitalize()

    @staticmethod
    def __calculate_combat_level_unfloored(levels: dict['Skills', int]) -> float:
        dominant_style = 1.3 * max(
            levels.get(Skills.ATTACK, 1) + levels.get(Skills.STRENGTH, 1),  # Attack + Strength
            2 * levels.get(Skills.MAGIC, 1),  # Magic
            2 * levels.get(Skills.RANGED, 1)  # Ranged
        )

        return 0.25 * (
                dominant_style
                + levels.get(Skills.DEFENCE, 1)  # Defence
                + levels.get(Skills.CONSTITUTION, 10)  # Constitution
                + floor(levels.get(Skills.PRAYER, 1) / 2)  # Prayer
                + floor(levels.get(Skills.SUMMONING, 1) / 2)   # Summoning
        )

    @staticmethod
    def xp_to_level(level: int, current_xp = 0) -> int:
        return max(0, Skills.min_xp_for_level(level) - current_xp)

    @staticmethod
    def calculate_combat_level(levels: dict['Skills', int]) -> int:
        return floor(Skills.__calculate_combat_level_unfloored(levels))

    # Adapted from https://runescape.wiki/w/Module:Combat_level
    @staticmethod
    def levels_for_combat_increase(levels: dict['Skills', int]) -> dict['Skills', int]:
        result = {
            Skills.ATTACK: 0,
            Skills.STRENGTH: 0,
            Skills.MAGIC: 0,
            Skills.RANGED: 0,
            Skills.DEFENCE: 0,
            Skills.CONSTITUTION: 0,
            Skills.PRAYER: 0,
            Skills.SUMMONING: 0
        }

        attack_strength_level = levels.get(Skills.ATTACK, 1) + levels.get(Skills.STRENGTH, 1)

        raw_combat_level = Skills.__calculate_combat_level_unfloored(levels)
        cb_fractional = raw_combat_level % 1
        result[Skills.CONSTITUTION] = result[Skills.DEFENCE] = ceil((1 - cb_fractional) * 4)
        result[Skills.PRAYER] = ceil(((1 - cb_fractional) * 4)) * 2 - (levels.get(Skills.PRAYER, 1) % 2)
        result[Skills.SUMMONING] = ceil(((1 - cb_fractional) * 4)) * 2 - (levels.get(Skills.SUMMONING, 1) % 2)

        if attack_strength_level >= 2*levels.get(Skills.MAGIC, 1) and attack_strength_level >= 2*levels.get(Skills.RANGED, 1):
            result[Skills.ATTACK] = result[Skills.STRENGTH] = ceil((1 - cb_fractional) / 0.325)
            result[Skills.MAGIC] = ceil(
                (attack_strength_level - 2*levels.get(Skills.MAGIC, 1)) / 2
                + (1 - cb_fractional) / 0.65
            )
            result[Skills.RANGED] = ceil(
                (attack_strength_level - 2*levels.get(Skills.RANGED, 1)) / 2
                + (1 - cb_fractional) / 0.65
            )
        else:
            result[Skills.ATTACK] = result[Skills.STRENGTH] = 2*max(levels.get(Skills.MAGIC, 1), levels.get(Skills.RANGED, 1))\
                                                              - attack_strength_level\
                                                              + ceil((1 - cb_fractional) / 0.325)
            result[Skills.MAGIC] = ceil((1 - cb_fractional) / 0.65)
            if levels.get(Skills.RANGED, 1) > levels.get(Skills.MAGIC, 1):
                result[Skills.RANGED] = result[Skills.MAGIC]
                result[Skills.MAGIC] = levels.get(Skills.RANGED, 1) - levels.get(Skills.MAGIC, 1) + result[Skills.RANGED]
            else:
                result[Skills.RANGED] = levels.get(Skills.MAGIC, 1) - levels.get(Skills.RANGED, 1) + result[Skills.MAGIC]

        return result
