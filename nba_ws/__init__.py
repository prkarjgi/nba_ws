from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse, fields, marshal
from nba_ws.celery import celery
from celery.schedules import crontab
import os
import json

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

api = Api(app)

from nba_ws.models import Tweet, SearchField
from nba_ws.tasks import get_data_async, get_data_periodic, SearchTweet
from auth import TwitterOAuth2


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


sf_format = {
    'search_field': fields.String,
    'author': fields.String,
    'datetime_added': fields.DateTime,
    'uri': fields.Url('search_field')
}

status_format = {
    'uri': fields.Url('taskstatus')
}


oauth = TwitterOAuth2()

celery.conf.beat_schedule = {
    'get-data-periodic': {
        'task': 'nba_ws.tasks.get_data_periodic',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (oauth.bearer_token,)
    },
}


class TweetListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'author',
            type=list,
            location='json'
        )
        super(TweetListAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        author = args['author']
        if author:
            tweets = Tweet.query.filter(
                Tweet.author.in_(author)
            ).order_by(Tweet.tweet_id.desc()).all()
        else:
            tweets = Tweet.query.order_by(Tweet.tweet_id.desc()).all()
        if not tweets:
            abort(404)
        formatted_tweets = [clean_tweet(tweet) for tweet in tweets]
        return jsonify({'tweets': formatted_tweets})


class SearchFieldAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldAPI, self).__init__()

    def get(self, search_id):
        search_field = SearchField.query.filter_by(
            id=search_id
        ).first()
        if not search_field:
            abort(404)
        resp = {}
        resp['search_field'] = json.loads(search_field.search_field)
        resp['author'] = search_field.author
        resp['datetime_added'] = search_field.datetime_added
        resp['search_id'] = search_id
        return {'sf': marshal(resp, sf_format)}

    def put(self, search_id):
        args = self.reqparse.parse_args()
        if not args['search_field']:
            abort(404)
        search_field = SearchField.query.filter_by(id=search_id).first()
        if not search_field:
            abort(404)
        search_field.search_field = json.dumps(args['search_field'])
        search_field.author = args['search_field']['q']['author']
        db.session.add(search_field)
        db.session.commit()
        return 202

    def delete(self, search_id):
        search_field = SearchField.query.filter_by(id=search_id).first()
        if not search_field:
            abort(404)
        db.session.delete(search_field)
        db.session.commit()
        return 202


class SearchFieldListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldListAPI, self).__init__()

    def get(self):
        search_fields = SearchField.query.order_by(SearchField.id.desc()).all()
        formatted_sf = [
            marshal(clean_search_field(sf), sf_format) for sf in search_fields
        ]
        return jsonify({'search_fields': formatted_sf})

    def post(self):
        args = self.reqparse.parse_args()
        sf = args['search_field']
        search_field = SearchField(json.dumps(sf), args['author'])
        db.session.add(search_field)
        db.session.commit()
        resp = {}
        resp['search_field'] = json.dumps(sf)
        resp['author'] = args['search_field']['q']['author']
        resp['datetime_added'] = search_field.datetime_added
        resp['search_id'] = search_field.id
        return {'sf': marshal(resp, sf_format)}, 201


class SearchTriggerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(SearchTriggerAPI, self).__init__()

    def get(self):
        bearer_token = TwitterOAuth2().bearer_token
        result = get_data_async.delay(bearer_token)
        # response = {'state': result.state}
        task = {'task_id': result.id}
        return jsonify({
            'Check task status at': marshal(task, status_format)
        })


class TaskStatusAPI(Resource):
    def __init__(self):
        super(TaskStatusAPI, self).__init__()

    def get(self, task_id):
        task = get_data_async.AsyncResult(task_id)
        if task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'ready': task.ready(),
                'result': task.result
            }
        else:
            response = {
                'state': task.state,
                'ready': task.ready()
            }
        return jsonify(response)


def clean_tweet(tweet_row):
    tweet = {}
    tweet['id'] = tweet_row.id
    tweet['tweet_id'] = tweet_row.tweet_id
    tweet['author'] = tweet_row.author
    tweet['author_id'] = tweet_row.author_id
    tweet['tweet_text'] = tweet_row.tweet_text
    tweet['tweet_date'] = tweet_row.tweet_date
    tweet['json_data'] = json.loads(tweet_row.json_data)
    tweet['search_params'] = json.loads(tweet_row.search_params)
    tweet['datetime_added'] = tweet_row.datetime_added
    return tweet


def clean_search_field(search_field_row):
    search_field = {}
    search_field['search_id'] = search_field_row.id
    search_field['search_field'] = json.loads(search_field_row.search_field)
    search_field['author'] = search_field_row.author
    search_field['datetime_added'] = search_field_row.datetime_added
    return search_field


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
