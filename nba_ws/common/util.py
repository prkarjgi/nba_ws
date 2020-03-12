"""This module contains helper classes, functions and objects used by the app.

Classes:
    TwitterOAuth2
    SearchTweet

Functions:
    clean_tweet
    clean_search_tweet

Objects:
    sf_format
    status_format
"""
import base64
from datetime import datetime
import json
import os
import requests

from flask_restful import fields
from urllib.parse import quote_plus, urljoin

from nba_ws import db
from nba_ws.models import Tweet


class TwitterOAuth2():
    """Generates OAuth2 bearer token used to authenticate Twitter API requests.

    Attributes:
        api_key: string used to store the escaped user's api key
            which are made safe for URL components.
        api_secret: string used to store the escaped user's api secret key
            which are made safe for URL components.
        bearer_token: string containing the OAuth2 token used to authenticate
            Twitter API transactions.
        creds_string: string of concatenated api_key and api_secret, separated
            by a colon(:).
        creds_bytes: bytes object of base64 encoded creds_string attribute.
        credentials: string type. Credentials object passed in header of
            request to generate the bearer token.
        invalidate_resp: requests.Response instance
    """
    def __init__(self):
        """
        """
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
        """Generates Twitter OAuth2 bearer token.

        """
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
        """Invalidates bearer token of class object.

        """
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
    """Class used to retrieve Tweets from the Twitter API.

    This class is used to perform requests to Twitter's Search API and write
    retrieved tweets to the Tweet model.

    Attributes:
        base_url: string, base URL of the Twitter API.
        headers: dict, header passed to request to generate bearer token.
        max_id: integer, parameter passed to Search API request, specifies
            that the tweets retrieved should not be greater than the max_id
            parameter passed into the request.
        params: dict, parameters passed to request to generate bearer token.
        rate_limit_status_url: string, URL of Twitter API to check the
            rate limit status for the user.
        search_url: string, URL with endpoint for Search API to retrieve tweets
        since_id: integer, parameter passed to Search API request, specifies
            that the tweets retrieved should be greater than the since_id
            parameter passed into the request.

    """
    def __init__(self, bearer_token):
        """Initializes attributes of class

        Args:
            bearer_token: string, OAuth2 token used to authenticate requests
            made to Twitter Search API.
        """
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
        """Gets the highest tweet id of a given author.

        Args:
            author: string, author of tweet to check the since_id for.
        """
        tweet = Tweet.query.filter_by(author=author).order_by(
            Tweet.tweet_id.desc()
        ).first()
        if tweet:
            self.since_id = str(tweet.tweet_id)

    def build_query(self, query_params):
        """Builds a query string used by the search request from a dictionary.

        Args:
            query_params: dict, containing keys mapped to values
                used by Twitter to refine the search request.

        Returns:
            Formatted query string to be passed as a search parameter to the
            Search API request.
        """
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
        """Adds keyword and value used by Twitter Search API to query string.

        Args:
            q: string, the query string passed to the search request.
            val: integer or string, to be mapped to a keyword.
            keyword: string, keyword used by Twitter Search API.

        Returns:
            The completed query string.
        """
        if q:
            q += ' '
        return q + f'{keyword}{val}'

    def build_params(self, search_params):
        """Builds a parameter dictionary that is passed to the search request.

        Args:
            search_params: dict, contains keys mapped to values used to
                construct a parameter dictionary that is passed to the search
                request.
            Sample format of search_params:
            {
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
        """Performs Search API requests for a given set of search parameters.

        This method is used to perform the search requests to retrieve tweets.
        To perform the search for given search parameters:
            1: Set the since_id for the search parameters.
            2: Form a dictionary payload from the search_params arg.
            3: Call the search method.
            4: If the response of the search is empty, stop and
                return the tweets list.
            5: If the response is not empty, format the response
                and add to the list to be returned.

        Args:
            search_params: dict, containing parameters provided to the
                Search API request.

        Returns:
            List of tweets, each tweet is stored as a dictionary with keys
            mapped to the raw json tweet data from the search method response
            and the search parameters used to perform that search request.
        """
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
        """Performs a Search API request to retrieve tweets.

        Returns:
            Dictionary of response from Search API request. Dictionary returned
            has keys mapped to the raw json data of the request and the
            search parameters used to perform the request.
        """
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
        """Gets the rate limit information.

        Args:
            resources: iterable, resources used as part of the payload
                for request to get rate limit status information.
                Default is None.

        Returns:
            json response of the request.
        """
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
        """Flattens tweet response into a tweet row to be added to Tweet model.

        Args:
            tweet_resp: dict, tweet response returned from the search method.

        Returns:
            Dictionary with keys corresponding to columns of the Tweet model
            mapped to corresponding values from tweet response object.
        """
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
        """Writes iterable tweets to Tweet model.

        Args:
            tweets: iterable, containing tweet responses
        """
        tweet_rows = [Tweet(**self.make_row(tweet)) for tweet in tweets]
        db.session.add_all(tweet_rows)
        db.session.commit()
        print(f"{len(tweet_rows)} record(s) added to table.")


def clean_tweet(tweet_row):
    """Create a dictionary from a row of Tweet model.

    Args:
        tweet_row: Tweet object, row of Tweet model.

    Returns:
        Dictionary containing data of row of Tweet model where each key
        is a column of the Tweet model mapped to their corresponding values.
    """
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
    """Clean Search Field row from SearchField model into a dictionary.

    Args:
        search_field_row: SearchField object, row of SearchField model.

    Returns:
        Dictionary containing data of row of SearchField model where each key
        is a column of the SearchField model mapped to their corresponding
        values.
    """
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
