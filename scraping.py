import requests
import json
import os
import base64
from urllib.parse import urljoin, quote_plus
from nba_news.models import Tweet
from nba_news import db
from celery_app import celery

base_url = 'https://api.twitter.com/'


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
                break
            tweet = {}
            tweet['json_data'] = resps['json_data']['statuses']
            tweet['search_params'] = resps['search_params']
        self.max_id = None
        return tweets

    def search(self):
        r = requests.get(
            url=self.search_url,
            params=self.params,
            headers=self.headers
        )
        print(r.url)
        assert r.status_code in [200]
        if r.json()['statuses']:
            self.max_id = min(
                [resp['id'] for resp in r.json()['statuses']]
            ) - 1
        response = {}
        response['json_data'] = r.json()
        response['search_params'] = self.params
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
        tweet_row = {}
        tweet_row['tweet_id'] = tweet_resp['json_data']['id']
        tweet_row['author'] = tweet_resp['json_data']['user']['screen_name']
        tweet_row['author_id'] = tweet_resp['json_data']['user']['id']
        tweet_row['json_data'] = json.dumps(tweet_resp['json_data'])
        tweet_row['search_params'] = str(tweet_resp['search_params'])
        return tweet_row

    def write_to_db(self, tweets):
        tweet_rows = [Tweet(**self.make_row(tweet)) for tweet in tweets]
        db.session.add_all(tweet_rows)
        db.session.commit()


def make_search_params(author, filters=None, hashtag=None, count=None):
    search_params = {}
    search_params['q'] = {}
    search_params['q']['author'] = author
    if count:
        search_params['count'] = str(count)
    if filters:
        search_params['q']['filters'] = filters
    if hashtag:
        search_params['q']['hashtag'] = hashtag
    return search_params


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


auth = TwitterOAuth2()

authors = [
    'wojespn',
    'ShamsCharania',
    'ZachLowe_NBA'
]


tweets = [get_tweets.delay(
    auth.bearer_token, make_search_params(author)
) for author in authors]


search_obj = SearchTweet(auth.bearer_token)

while(1):
    ready = [tweet.result for tweet in tweets if tweet.ready()]
    if len(ready) == len(authors):
        break

for each in ready[1]:
    print(each.keys())
search_obj.write_to_db(ready[1])
