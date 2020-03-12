"""Contains API Resource for listing Tweets in database.

This module contains an API class for listing tweets stored in the Tweet model
in the database - TweetListAPI
"""
from flask import abort, jsonify
from flask_restful import Resource, reqparse

from nba_ws.common.util import clean_tweet
from nba_ws.models import Tweet


class TweetListAPI(Resource):
    """API to list Tweets stored in Tweet model.

    HTTP Methods supported: GET.

    Attributes:
        reqparse: instance of the reqparse.RequestParser class used to validate
            data parameters passed in the request.
    """
    def __init__(self):
        """Creates attributes and runs Resource class constructor.

        Argument(s) added to the reqparse:
            author
        """
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'author',
            type=list,
            location='json'
        )
        super(TweetListAPI, self).__init__()

    def get(self):
        """Returns tweets stored in Tweet model.

        If any parameters are passed to the request, the tweets are filtered
        accordingly. If no parameters are passed, then all tweets are fetched.

        Returns:
            A json serialized dictionary containing a key 'tweets' mapped to
            the tweets fetched according to the parameters passed to the
            request. Tweets are formatted according to the clean_tweet object
            (see clean_tweet from nba_ws.common.util for more details).

        Raises:
            HTTPError: If no tweets are returned by query.
        """
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
