import requests
from requests_oauthlib import OAuth1
import json
import os
import base64
from urllib.parse import urljoin, quote_plus
from nba_news.models import Tweet

base_url = 'https://api.twitter.com/'


class Twitter_OAuth2():
    def __init__(self):
        # d
        self.api_key = quote_plus(os.getenv('TWITTER_API_KEY'))
        self.api_secret = quote_plus(os.getenv('TWITTER_API_SECRET'))

        # d
        self.bearer_token = os.getenv('BEARER_TOKEN', None)

        # d
        self.creds_string = f'{self.api_key}:{self.api_secret}'
        self.creds_bytes = base64.b64encode(self.creds_string.encode('utf-8'))
        self.credentials = self.creds_bytes.decode('utf-8')

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
        self.invalidate_resp = r


class SearchTweet():
    def __init__(self, bearer_token):
        self.search_url = "https://api.twitter.com/1.1/search/tweets.json"
        self.params = {}
        self.headers = {'Authorization': f'Bearer {bearer_token}'}

    def search(self, params):
        r = requests.get(
            url=self.search_url,
            params=params,
            headers=self.headers
        )
        assert r.status_code in [200]
        return r.json()


oauth2 = Twitter_OAuth2()
if not oauth2.bearer_token:
    oauth2.get_oauth2_bearer_token()


params = {
    'q': 'from:ShamsCharania -filter:retweets',
    'count': '40'
}

headers = {
    'Authorization': f'Bearer {oauth2.bearer_token}'
}

# resp1 = requests.get(url=res_url, params=params, headers=headers)
# print(json.dumps(resp1.json(), indent=4))
