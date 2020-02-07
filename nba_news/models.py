from nba_news import db
from datetime import datetime


class Tweet(db.Model):
    __tablename__ = 'nba-news-tweet'
    id = db.Column()
    tweet_id = db.Column()
    author = db.Column()
    json_data = db.Column()
    datetime_added = db.Column()

    def __init__(self, tweet_id, author, json_data):
        self.tweet_id = tweet_id
        self.author = author
        self.json_data = json_data
