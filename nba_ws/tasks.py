"""Module containing Celery tasks used in the application.

Tasks defined:
    get_tweets: retrieve all new tweets for a given search parameter arg.
    get_data_periodic: retrieves all new tweets for all SearchField rows run
        periodically by the celery beat(see nba_ws.celery.py for more details).
    get_data_async: retrieves all new tweets for all SearchField rows,
        which can be run manually using the SearchTriggerAPI web resource
        (see class SearchTriggerAPI from nba_ws.resources.search for more
        details).
"""
from functools import reduce
import json

from nba_ws import celery
# from nba_ws.celery import celery
from nba_ws.models import SearchField
from nba_ws.common.util import SearchTweet


@celery.task
def get_tweets(bearer_token, search_params):
    """Function used to search for new Tweets of a Search Field.

    This function is used for performing a Search API request to retrieve
    new tweets for a given search_param argument.

    Args:
        bearer_token: string, OAuth2 token used to authenticate requests made
            to Twitter Search API.
        search_params: dict, parameters passed to the request to Search API.

    Returns:
        List of tweets(each tweet is stored as a dict).
    """
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
    """Function used to retrieve new tweets for all Search Fields.

    This function is used by celery beat to periodically search Twitter for
    new tweets by any of the Search Fields.

    Args:
        bearer_token: string, OAuth2 token used to authenticate requests made
            to Twitter Search API.

    Returns:
        None
    """
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
    """Function used to retrieve new tweets for all Search Fields.

    This function is used by the SearchTriggerAPI resource of the application
    to manually run a search to retrieve new tweets for all Search Fields in
    the SearchField model.

    Args:
        bearer_token: string, OAuth2 token used to authenticate requests made
            to Twitter Search API.

    Returns:
        None
    """
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
