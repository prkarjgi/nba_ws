from nba_ws.celery import celery
from nba_ws.models import SearchField
from nba_ws.common.util import SearchTweet
from functools import reduce
import json
# import logging

# logging.basicConfig(filename='tasks.log')
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)


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
