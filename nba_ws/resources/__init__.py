"""The 'resources' subpackage contains the API resource exposed endpoints.

"""
from flask import Blueprint
from flask_restful import Api

from nba_ws.resources.search import SearchTriggerAPI, TaskStatusAPI
from nba_ws.resources.search_field import SearchFieldAPI, SearchFieldListAPI
from nba_ws.resources.tweet import TweetListAPI

base_uri = '/todo/api/v1.0'
api_bp = Blueprint('resources', __name__)
api = Api(api_bp)


api.add_resource(
    TweetListAPI,
    f'{base_uri}/tweets',
    endpoint='tweets'
)
api.add_resource(
    SearchFieldListAPI,
    f'{base_uri}/search_field/all',
    endpoint='search_fields'
)
api.add_resource(
    SearchFieldAPI,
    f'{base_uri}/search_field/<int:search_id>',
    endpoint='search_field'
)
api.add_resource(
    SearchTriggerAPI,
    f'{base_uri}/search/trigger',
    endpoint='search_trigger'
)
api.add_resource(
    TaskStatusAPI,
    f'{base_uri}/search/taskstatus/<task_id>',
    endpoint='taskstatus'
)
