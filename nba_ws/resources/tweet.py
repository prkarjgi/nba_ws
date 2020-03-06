from flask import abort, jsonify
from flask_restful import Resource, reqparse
from nba_ws.models import Tweet
from nba_ws.common.util import clean_tweet


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
            abort(404, description='Not found')
        formatted_tweets = [clean_tweet(tweet) for tweet in tweets]
        return jsonify({'tweets': formatted_tweets})
