from flask import Flask, render_template, request
from werkzeug.datastructures import ImmutableMultiDict

import service
from service.model import SkillSet, Skills

app = Flask(__name__)


@app.route('/')
def home():
    quests = service.get_quest_data()
    return render_template('index.html', quests=quests, skills=Skills)


def parse_initial_stats(form_data: ImmutableMultiDict[str, str]):
    result = SkillSet()

    for skill in result:
        type = form_data.get(f'skill{str(skill)}Type', None)
        value = form_data.get(f'skill{str(skill)}Value', '0')
        value = int(value) if value else 0
        if type == 'level':
            value = Skills.min_xp_for_level(int(value))
        result[skill] = max(result[skill], value)

    return result


@app.route('/result', methods=['POST'])
def result():
    initial_stats = parse_initial_stats(request.form)
    completed_quests = [int(quest_id) for form_name, quest_id in request.form.items() if form_name.startswith('quest_')]
    strategy = service.get_optimal_quest_strategy(initial_quests=completed_quests, initial_stats=initial_stats)
    return render_template('result.html', strategy=strategy)
