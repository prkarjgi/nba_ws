from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from nba_ws.celery import celery
from celery.schedules import crontab
import os


app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

api = Api(app)

from nba_ws.models import Tweet, SearchField
from nba_ws.tasks import get_data_async, get_data_periodic
from nba_ws.errors import handlers
from nba_ws.common.util import TwitterOAuth2
from nba_ws.resources.search import SearchTriggerAPI, TaskStatusAPI,\
    SearchFieldAPI, SearchFieldListAPI
from nba_ws.resources.tweet import TweetListAPI


oauth = TwitterOAuth2()

celery.conf.beat_schedule = {
    'get-data-periodic': {
        'task': 'nba_ws.tasks.get_data_periodic',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (oauth.bearer_token,)
    },
}


api.add_resource(
    TweetListAPI,
    '/todo/api/v1.0/tweets',
    endpoint='tweets'
)
api.add_resource(
    SearchFieldListAPI,
    '/todo/api/v1.0/search',
    endpoint='search_fields'
)
api.add_resource(
    SearchFieldAPI,
    '/todo/api/v1.0/search/<int:search_id>',
    endpoint='search_field'
)
api.add_resource(
    SearchTriggerAPI,
    '/todo/api/v1.0/search/trigger',
    endpoint='search_trigger'
)
api.add_resource(
    TaskStatusAPI,
    '/todo/api/v1.0/taskstatus/<task_id>',
    endpoint='taskstatus'
)

db.create_all()
