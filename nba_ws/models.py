"""Module used to define the Database Models used in the application.

Models:
    Tweet: stores Tweets returned by Search API requests.
    SearchField: stores Search Field values passes while performing
        Search API requests.
"""
from datetime import datetime

from nba_ws import db


class Tweet(db.Model):
    """Model used to store Tweets from Search API requests.

    Attributes:
        tweet_id: integer, id of tweet as per Twitter.
        author: string, author of tweet.
        author_id: integer, id of author of tweet as per Twitter.
        tweet_text: string, text content of Tweet.
        tweet_date: datetime, UTC date of tweet being posted.
        json_data: json, entire Search API response data stored as a json
            column. This column is the raw data of the response.
        search_params: json, the parameters passed to the Search API request
            to retrieve the tweet from Twitter.
    """
    __tablename__ = 'nba-ws-tweet'
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, unique=True, nullable=False)
    author = db.Column(db.String())
    author_id = db.Column(db.Integer)
    tweet_text = db.Column(db.String())
    tweet_date = db.Column(db.DateTime)
    json_data = db.Column(db.Text)
    search_params = db.Column(db.Text)
    datetime_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(
        self, tweet_id, author, author_id,
        tweet_text, tweet_date, json_data, search_params
    ):
        self.tweet_id = tweet_id
        self.author = author
        self.author_id = author_id
        self.tweet_text = tweet_text
        self.tweet_date = tweet_date
        self.json_data = json_data
        self.search_params = search_params

    def __repr__(self):
        return f"<Tweet({self.id}, {self.author}, {self.tweet_id})>"


class SearchField(db.Model):
    """Model used to store Search Fields.

    Search Fields are parameters that are provided to the Twitter API
    while using the Search API to refine the tweets returned.

    Search Fields are used for periodic Twitter API searches and
    manually triggered searches.

    Attributes:
        __tablename__: string, name of the table.
        author: string, author in search_field column.
        search_field: json object, dictionary containing search_field
            parameters serialized to json.
    """
    __tablename__ = 'nba-ws-search_field'
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(), unique=True)
    search_field = db.Column(db.Text, unique=True)
    datetime_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, search_field, author):
        self.search_field = search_field
        self.author = author

    def __repr__(self):
        return f"<SearchField({self.id}, {self.search_field})>"
