from nba_ws import db
from datetime import datetime


class Tweet(db.Model):
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
