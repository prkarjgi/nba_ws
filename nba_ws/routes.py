from flask import render_template, url_for, request
from nba_ws import app, db
from nba_ws.models import Tweet


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template()
    tweets = Tweet.query.filter_by()
    return render_template('index.html', tweets=tweets)
