from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os
import json

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

api = Api(app)

from nba_ws.models import Tweet, SearchField


class TweetListAPI(Resource):
    def __init__(self):
        pass

    def get(self):
        tweets = Tweet.query.order_by(Tweet.tweet_id.desc()).all()
        formatted_tweets = [clean_tweet(tweet) for tweet in tweets]
        return jsonify({'tweets': formatted_tweets})


class SearchFieldAPI(Resource):
    def __init__(self):
        pass

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


class SearchFieldListAPI(Resource):
    def __init__(self):
        pass

    def get(self):
        search_fields = SearchField.query.order_by(SearchField.id.desc()).all()
        formatted_sf = [clean_search_field(sf) for sf in search_fields]
        return jsonify({'search_fields': formatted_sf})

    def post(self):
        pass


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
    search_field['id'] = search_field_row.id
    search_field['search_field'] = json.loads(search_field_row.search_field)
    search_field['datetime_added'] = search_field_row.datetime_added
    return search_field


api.add_resource(TweetListAPI, '/todo/api/v1.0/tweets', endpoint='tweets')
api.add_resource(
    SearchFieldListAPI, '/todo/api/v1.0/search', endpoint='search_fields'
)
api.add_resource(
    SearchFieldAPI, '/todo/api/v1.0/search/<int:id>', endpoint='search_field'
)

db.create_all()
