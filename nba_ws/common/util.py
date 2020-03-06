from urllib.parse import quote_plus, urljoin
from flask_restful import fields
from nba_ws import db
from nba_ws.models import Tweet
from datetime import datetime
import requests
import json
import os
import base64


class TwitterOAuth2():
    def __init__(self):
        # get consumer key and consumer secret key environment variables
        self.api_key = quote_plus(os.getenv('TWITTER_API_KEY'))
        self.api_secret = quote_plus(os.getenv('TWITTER_API_SECRET'))

        # get existing bearer token from environment variable
        # return None if it doesn't exist
        self.bearer_token = os.getenv('BEARER_TOKEN', None)

        # create a credentials string
        # encode credentials string to bytes and then to base64 encoding
        # decode bytes credentials to utf-8 string
        self.creds_string = f'{self.api_key}:{self.api_secret}'
        self.creds_bytes = base64.b64encode(self.creds_string.encode('utf-8'))
        self.credentials = self.creds_bytes.decode('utf-8')

        # check if bearer_token is None
        if self.bearer_token is None:
            self.get_oauth2_bearer_token()

    def get_oauth2_bearer_token(self):
        headers = {
            'Authorization': f'Basic {self.credentials}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        body = {'grant_type': 'client_credentials'}
        resource_url = 'https://api.twitter.com/oauth2/token'
        r = requests.post(url=resource_url, data=body, headers=headers)
        assert r.status_code in [200]
        self.bearer_token = r.json()['access_token']

    def invalidate_oauth2_bearer_token(self):
        resource_url = 'https://api.twitter.com/oauth2/invalidate_token'
        headers = {
            'Authorization': f'Basic {self.credentials}'
            # 'Content-Type': 'application/x-www-form-urlencoded;'
        }
        data = {'access_token': self.bearer_token}
        r = requests.post(url=resource_url, data=data, headers=headers)
        assert r.status_code in [200]
        self.invalidate_resp = r


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


sf_format = {
    'search_field': fields.String,
    'author': fields.String,
    'datetime_added': fields.DateTime,
    'uri': fields.Url('resources.search_field', absolute=True)
}

status_format = {
    'task_status_uri': fields.Url('resources.taskstatus', absolute=True)
}
