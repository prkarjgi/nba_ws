from flask import Blueprint
from flask_restful import Api
from nba_ws.resources.search import SearchFieldAPI,\
    SearchFieldListAPI, SearchTriggerAPI, TaskStatusAPI
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
    f'{base_uri}/search',
    endpoint='search_fields'
)
api.add_resource(
    SearchFieldAPI,
    f'{base_uri}/search/<int:search_id>',
    endpoint='search_field'
)
api.add_resource(
    SearchTriggerAPI,
    f'{base_uri}/search/trigger',
    endpoint='search_trigger'
)
api.add_resource(
    TaskStatusAPI,
    f'{base_uri}/taskstatus/<task_id>',
    endpoint='taskstatus'
)
