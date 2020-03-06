from flask import Blueprint
from flask_restful import Api
from nba_ws.resources.search import SearchFieldAPI,\
    SearchFieldListAPI, SearchTriggerAPI, TaskStatusAPI
from nba_ws.resources.tweet import TweetListAPI


api_bp = Blueprint('resources', __name__)
api = Api(api_bp)


api.add_resource(
    TweetListAPI,
    '/todo/api/v1.0/tweets',
    endpoint='tweets'
)
api.add_resource(
    SearchFieldListAPI,
    '/todo/api/v1.0/search',
    endpoint='search_fields'
)
api.add_resource(
    SearchFieldAPI,
    '/todo/api/v1.0/search/<int:search_id>',
    endpoint='search_field'
)
api.add_resource(
    SearchTriggerAPI,
    '/todo/api/v1.0/search/trigger',
    endpoint='search_trigger'
)
api.add_resource(
    TaskStatusAPI,
    '/todo/api/v1.0/taskstatus/<task_id>',
    endpoint='taskstatus'
)
