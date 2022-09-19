from flask import Flask, render_template, request

import service

app = Flask(__name__)


@app.route('/')
def home():
    quests = service.get_quest_data()
    return render_template('index.html', quests=quests)


@app.route('/result', methods=['POST'])
def result():
    completed_quests = [int(quest_id) for _, quest_id in request.form.items()]
    strategy = service.get_optimal_quest_strategy(initial_quests=completed_quests)
    return render_template('result.html', strategy=strategy)
