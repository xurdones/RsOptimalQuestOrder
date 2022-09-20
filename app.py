from flask import Flask, render_template, request
from werkzeug.datastructures import ImmutableMultiDict

import service
from service.model import SkillSet, Skills

app = Flask(__name__)


@app.route('/')
def home():
    quests = service.get_quest_data()
    return render_template('index.html', quests=quests)


def parse_initial_stats(form_data: ImmutableMultiDict[str, str]):
    result = {
        'Attack': 0,
        'Strength': 0,
        'Defence': 0,
        'Ranged': 0,
        'Prayer': 0,
        'Magic': 0,
        'Runecrafting': 0,
        'Construction': 0,
        'Dungeoneering': 0,
        'Archaeology': 0,
        'Constitution': 0,
        'Agility': 0,
        'Herblore': 0,
        'Thieving': 0,
        'Crafting': 0,
        'Fletching': 0,
        'Slayer': 0,
        'Hunter': 0,
        'Divination': 0,
        'Mining': 0,
        'Smithing': 0,
        'Fishing': 0,
        'Cooking': 0,
        'Firemaking': 0,
        'Woodcutting': 0,
        'Farming': 0,
        'Summoning': 0
    }

    for skill in result:
        type = form_data.get(f'skill{skill}Type', None)
        value = form_data.get(f'skill{skill}Value', '0')
        if not value:
            value = '0'
        if type == 'xp':
            result[skill] = int(value)
        elif type == 'level':
            result[skill] = Skills.min_xp_for_level(int(value))

    return result


@app.route('/result', methods=['POST'])
def result():
    initial_stats = parse_initial_stats(request.form)
    completed_quests = [int(quest_id) for form_name, quest_id in request.form.items() if form_name.startswith('quest_')]
    strategy = service.get_optimal_quest_strategy(initial_quests=completed_quests, initial_stats=initial_stats)
    return render_template('result.html', strategy=strategy)
