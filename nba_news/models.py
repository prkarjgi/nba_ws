from nba_news import db
from datetime import datetime


class Tweet(db.Model):
    __tablename__ = 'nba-news-tweet'
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, unique=True, nullable=False)
    author = db.Column(db.String())
    author_id = db.Column(db.Integer)
    json_data = db.Column(db.Text)
    search_params = db.Column(db.Text)
    datetime_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, tweet_id, author, author_id, json_data, search_params):
        self.tweet_id = tweet_id
        self.author = author
        self.author_id = author_id
        self.json_data = json_data
        self.search_params = search_params

    def __repr__(self):
        return f"<Tweet({self.id}, {self.author}, {self.tweet_id})>"
