import requests
from requests_oauthlib import OAuth1
import json
import os
import base64
from urllib.parse import urljoin, quote_plus
from nba_news.models import Tweet
from nba_news import db

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

        # check if bearer_token is not None
        if self.bearer_token is not None:
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

    def make_query(self, author, filters=None):
        q = ''
        if author:
            q = f'from:{author}'
        if filters:
            if q:
                q += ' '
            q += f'-filters:{filters}'
        return q

    def make_params(self, author, filters=None, count=None):
        if self.since_id:
            self.params['since_id'] = self.since_id
        if self.max_id:
            self.params['max_id'] = self.max_id
        if count:
            self.params['count'] = str(count)
        self.params['q'] = self.make_query(author, filters)

    def get_tweets(self, author, filters, count):
        tweets = []
        self.get_since_id(author)
        while(1):
            self.make_params(author, filters, count)
            resps = self.search()
            if not resps['statuses']:
                break
            tweets.append(resps['statuses'])
            self.max_id = min([resp['id'] for resp in resps['statuses']]) - 1
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
        return r.json()

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
        tweet_row['tweet_id'] = tweet_resp['id']
        tweet_row['author'] = tweet_resp['user']['screen_name']
        tweet_row['author_id'] = tweet_resp['user']['id']
        tweet_row['json_data'] = json.dumps(tweet_resp)
        return tweet_row

    def write_to_db(self, tweets):
        tweet_rows = [Tweet(**self.make_row(tweet)) for tweet in tweets]
        db.session.add_all(tweet_rows)
        db.session.commit()

# params = {
#     'q': 'from:ShamsCharania -filter:retweets',
#     'count': '40'
# }

# ZachLowe_NBA


auth = TwitterOAuth2()
search_object = SearchTweet(auth.bearer_token)
resp = search_object.get_tweets(
    author='wojespn', filters='retweets', count=2
)

# with open('response_json.json', 'w') as fh:
#     json.dump(resp, fh, indent=4)

print(resp)
print(len(resp))

# tweets = resp['statuses']
# print(tweets)
# search_object.write_to_db(tweets)
