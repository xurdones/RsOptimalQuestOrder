from collections import Counter
from math import ceil

from .skills import Skills


class SkillSet(Counter):
    def __init__(self, iterable=None):
        iterable = iterable or {skill: skill.initial for skill in Skills}
        super(SkillSet, self).__init__(iterable)

    def __lt__(self, other):
        if isinstance(other, SkillSet):
            return all(self.get(skill, 0) < other[skill] for skill in other)
        raise NotImplementedError

    def __le__(self, other):
        if isinstance(other, SkillSet):
            return all(self.get(skill, 0) <= other[skill] for skill in other)
        raise NotImplementedError

    def total(self) -> int:
        return sum(self.values())

    @classmethod
    def empty(cls):
        return super(SkillSet, cls).__new__(cls)

    @staticmethod
    def from_json(data) -> 'SkillSet':
        return SkillSet({Skills[req["skill"].upper()]: Skills.min_xp_for_level(req["level"]) for req in data})

    @staticmethod
    def optimal_route_to_combat_level(goal: int, current_stats: 'SkillSet' = None) -> 'SkillSet':
        route = SkillSet.empty()
        if goal < 3:
            return route
        if goal > 138:
            raise ValueError
        if goal == 3:
            return SkillSet()

        current_stats = current_stats or SkillSet()

        combat_level = Skills.calculate_combat_level({skill: Skills.level_for_xp(xp) for skill, xp in current_stats.items()})
        while combat_level < goal:
            levels_to_next_cb = Skills.levels_for_combat_increase(
                {skill: Skills.level_for_xp(xp) for skill, xp in current_stats.items()}
            )
            training_to_levels = Counter()
            for skill, level_req in levels_to_next_cb.items():
                if skill in Skills.CONSTITUTION | Skills.DEFENCE:
                    higher, lower = SkillSet.__get_higher_and_lower_of_skills(
                        current_stats,
                        Skills.CONSTITUTION,
                        Skills.DEFENCE)
                    training_to_levels[higher], training_to_levels[lower] = SkillSet.__advance_levels_in_step(
                        current_stats,
                        higher,
                        level_req,
                        lower
                    )
                elif skill in Skills.ATTACK | Skills.STRENGTH:
                    higher, lower = SkillSet.__get_higher_and_lower_of_skills(
                        current_stats,
                        Skills.ATTACK,
                        Skills.STRENGTH
                    )
                    training_to_levels[higher], training_to_levels[lower] = SkillSet.__advance_levels_in_step(
                        current_stats,
                        higher,
                        level_req,
                        lower
                    )
                else:
                    training_to_levels[skill] = Skills.xp_to_level(
                        min(Skills.level_for_xp(current_stats[skill]) + level_req, 99),
                        current_stats[skill]
                    )

            strategy = SkillSet.choose_training_strategy(training_to_levels)
            current_stats += strategy
            route += strategy
            combat_level = Skills.calculate_combat_level({skill: Skills.level_for_xp(xp) for skill, xp in current_stats.items()})
        return route

    @staticmethod
    def __advance_levels_in_step(current_stats: 'SkillSet', higher: Skills, level_req: int, lower: Skills) -> (int, int):
        level_gap = Skills.level_for_xp(current_stats[higher]) - Skills.level_for_xp(current_stats[lower])
        levels_to_close_gap = min(level_gap, level_req)
        training_for_lower = Skills.xp_to_level(
            min(99, Skills.level_for_xp(current_stats[lower]) + ceil(
                levels_to_close_gap + max(level_req - level_gap, 0) / 2)),
            current_stats[lower]
        )
        training_for_higher = Skills.xp_to_level(
            min(99, Skills.level_for_xp(current_stats[higher]) + max(level_req - level_gap, 0) // 2),
            current_stats[higher]
        )

        return training_for_higher, training_for_lower

    @staticmethod
    def __get_higher_and_lower_of_skills(current_stats: 'SkillSet', first: Skills, second: Skills) -> (Skills, Skills):
        return (first, second) if current_stats[first] >= current_stats[second] else (second, first)

    @staticmethod
    def choose_training_strategy(xp_requirements: Counter[Skills, int]) -> 'SkillSet':
        chosen_skill, chosen_xp = xp_requirements.most_common()[-1]

        if chosen_skill in Skills.ATTACK | Skills.STRENGTH:
            chosen_xp = xp_requirements[Skills.ATTACK] + xp_requirements[Skills.STRENGTH]
        elif chosen_skill in Skills.CONSTITUTION | Skills.DEFENCE:
            chosen_xp = xp_requirements[Skills.CONSTITUTION] + xp_requirements[Skills.DEFENCE]

        for skill, xp in xp_requirements.items():
            target_xp = xp
            if skill in Skills.ATTACK | Skills.STRENGTH:
                target_xp = xp_requirements[Skills.ATTACK] + xp_requirements[Skills.STRENGTH]
            elif skill in Skills.CONSTITUTION | Skills.DEFENCE:
                target_xp = xp_requirements[Skills.CONSTITUTION] + xp_requirements[Skills.DEFENCE]

            if target_xp < chosen_xp:
                chosen_xp = target_xp
                chosen_skill = skill

        result = {}
        if chosen_skill in Skills.ATTACK | Skills.STRENGTH:
            result = {Skills.ATTACK: xp_requirements[Skills.ATTACK], Skills.STRENGTH: xp_requirements[Skills.STRENGTH]}
        elif chosen_skill in Skills.CONSTITUTION | Skills.DEFENCE:
            result = {Skills.CONSTITUTION: xp_requirements[Skills.CONSTITUTION], Skills.DEFENCE: xp_requirements[Skills.DEFENCE]}
        else:
            result = {chosen_skill: chosen_xp}

        return SkillSet(result)
