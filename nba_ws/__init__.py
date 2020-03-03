from flask import Flask, jsonify, abort, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse, fields, marshal
from celery import Celery
from celery.schedules import crontab
from functools import reduce
from datetime import datetime
from urllib.parse import urljoin
import os
import json
import requests

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

api = Api(app)
celery = Celery(
    'nba_ws',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

from nba_ws.models import Tweet, SearchField
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


class SearchTweet():
    def __init__(self, bearer_token):
        self.base_url = "https://api.twitter.com/1.1/"
        self.search_url = urljoin(self.base_url, "search/tweets.json")
        self.rate_limit_status_url = urljoin(
            self.base_url, "application/rate_limit_status.json"
        )
        self.params = {}
        self.headers = {'Authorization': f'Bearer {bearer_token}'}
        self.since_id = None
        self.max_id = None

    def get_since_id(self, author):
        tweet = Tweet.query.filter_by(author=author).order_by(
            Tweet.tweet_id.desc()
        ).first()
        if tweet:
            self.since_id = str(tweet.tweet_id)

    def build_query(self, query_params):
        q = ''
        for key, val in query_params.items():
            if key == 'author':
                q = self.add_val(q, val, 'from:')
            if key == 'filters':
                q = self.add_val(q, val, '-filters:')
            if key == 'hashtag':
                q = self.add_val(q, val, '#')
        return q

    def add_val(self, q, val, keyword):
        if q:
            q += ' '
        return q + f'{keyword}{val}'

    def build_params(self, search_params):
        """
            search params format - {
                'q': {
                    'author': <name of author>,
                    ['filters': <filter tweets>],
                    ['hashtag': <#hashtag>]
                },
                ['count':<number of tweets to fetch>]
            }
        """
        if self.since_id:
            self.params['since_id'] = self.since_id
        if self.max_id:
            self.params['max_id'] = self.max_id
        if search_params.get('count', None):
            self.params['count'] = str(search_params.get('count'))
        if search_params.get('q'):
            self.params['q'] = self.build_query(search_params['q'])

    def get_tweets(self, search_params):
        tweets = []
        self.get_since_id(search_params['q']['author'])
        while(1):
            self.build_params(search_params)
            resps = self.search()
            if not resps['json_data']['statuses']:
                self.max_id = None
                break
            for status in resps['json_data']['statuses']:
                tweet = {}
                tweet['json_data'] = status
                tweet['search_params'] = resps['search_params']
                tweets.append(tweet)
        return tweets

    def search(self):
        r = requests.get(
            url=self.search_url,
            params=self.params,
            headers=self.headers
        )
        print(r.url, r.status_code)
        assert r.status_code in [200]
        if r.json()['statuses']:
            self.max_id = min(
                [resp['id'] for resp in r.json()['statuses']]
            ) - 1
        response = {}
        response['json_data'] = r.json()
        response['search_params'] = self.params
        self.params = {}
        return response

    def get_rate_limit_status(self, resources=None):
        payload = {}
        if resources:
            payload = {'resources': ','.join(resources)}
        r = requests.get(
            url=self.rate_limit_status_url,
            params=payload,
            headers=self.headers
        )
        assert r.status_code in [200]
        return r.json()

    def make_row(self, tweet_resp):
        # "Fri Feb 07 16:27:35 +0000 2020"
        tweet_row = {}
        tweet_row['tweet_id'] = tweet_resp['json_data']['id']
        tweet_row['author'] = tweet_resp['json_data']['user']['screen_name']
        tweet_row['author_id'] = tweet_resp['json_data']['user']['id']
        tweet_row['tweet_text'] = tweet_resp['json_data']['text']
        tweet_row['tweet_date'] = datetime.strptime(
            tweet_resp['json_data']['created_at'], "%a %b %d %H:%M:%S %z %Y"
        )
        tweet_row['json_data'] = json.dumps(tweet_resp['json_data'])
        tweet_row['search_params'] = json.dumps(tweet_resp['search_params'])
        return tweet_row

    def write_to_db(self, tweets):
        tweet_rows = [Tweet(**self.make_row(tweet)) for tweet in tweets]
        db.session.add_all(tweet_rows)
        db.session.commit()
        print(f"{len(tweet_rows)} record(s) added to table.")


@celery.task
def get_tweets(bearer_token, search_params):
    search_object = SearchTweet(bearer_token)
    tweets = []
    search_object.get_since_id(search_params['q']['author'])
    while(1):
        search_object.build_params(search_params)
        resps = search_object.search()
        if not resps['json_data']['statuses']:
            break
        for status in resps['json_data']['statuses']:
            tweet = {}
            tweet['json_data'] = status
            tweet['search_params'] = resps['search_params']
            tweets.append(tweet)
    search_object.max_id = None
    return tweets


oauth = TwitterOAuth2()

celery.conf.beat_schedule = {
    'get-data-periodic': {
        'task': 'nba_ws.get_data_periodic',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (oauth.bearer_token,)
    },
}


@celery.task
def get_data_periodic(bearer_token):
    search_obj = SearchTweet(bearer_token)
    search_params = SearchField.query.all()
    tweets = [
        search_obj.get_tweets(
            json.loads(search_param.search_field)
        ) for search_param in search_params
    ]
    data = list(reduce(lambda x, y: x + y, tweets))
    if len(data) > 0:
        search_obj.write_to_db(data)


@celery.task(bind=True)
def get_data_async(self, bearer_token):
    search_obj = SearchTweet(bearer_token)
    search_params = SearchField.query.all()
    tweets = [
        get_tweets.delay(
            bearer_token, json.loads(search_param.search_field)
        ) for search_param in search_params
    ]
    while(1):
        ready = [tweet.result for tweet in tweets if tweet.ready()]
        if len(ready) == len(tweets):
            break
    data = list(reduce(lambda x, y: x + y, ready))
    if len(data) > 0:
        search_obj.write_to_db(data)


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
