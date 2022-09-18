from flask import Flask, render_template, jsonify

import service

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/result', methods=['POST'])
def result():
    strategy = service.get_optimal_quest_strategy()
    return render_template('result.html', strategy=strategy)
