from nba_ws import db, app
from nba_ws.celery import celery
from nba_ws.models import SearchField, Tweet
from functools import reduce
from datetime import datetime
from urllib.parse import urljoin
import json
import requests
import logging

logging.basicConfig(filename='tasks.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
