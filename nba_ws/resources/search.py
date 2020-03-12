"""Contains API Resources used to search Twitter for NBA news.

This module contains 2 Resource classes which are used for searching Twitter:
    SearchTriggerAPI
    TaskStatusAPI
"""
from flask import abort, jsonify
from flask_restful import Resource, marshal, reqparse

from nba_ws.common.util import TwitterOAuth2, status_format
from nba_ws.tasks import get_data_async


class SearchTriggerAPI(Resource):
    """This API is used to manually trigger the get_data_async task.

    HTTP Methods supported: GET.

    Performing a GET request on the endpoint will trigger the search
    functionality to search Twitter using the search fields in the SearchField
    model and add new tweets to the Tweet model.

    Attributes:
        reqparse: instance of the reqparse.RequestParser class used to validate
            data parameters passed in the request.
    """
    def __init__(self):
        """Creates the reqparse attribute and inits the Resource class
        """
        self.reqparse = reqparse.RequestParser()
        super(SearchTriggerAPI, self).__init__()

    def get(self):
        """Triggers the get_data_async celery task and returns task details.

        Returns:
            A dictionary containing data about a task as specified by
            status_format (See nba_ws.common.util for status_format),
            which is serialized to json and returned.
        """
        bearer_token = TwitterOAuth2().bearer_token
        result = get_data_async.delay(bearer_token)
        task = {
            'task_id': result.id
        }
        return jsonify({
            'task_details': marshal(task, status_format)
        })


class TaskStatusAPI(Resource):
    """This API is used to monitor the status of the triggered get_async_data task.

    HTTP Methods supported: GET.
    """
    def __init__(self):
        """Inits Resource class constructor
        """
        super(TaskStatusAPI, self).__init__()

    def get(self, task_id):
        """Returns a response containing the state, ready status and result
        of a task.

        Args:
            task_id: string which corresponds to the task to be checked.

        Returns:
            A dictionary containing data on the task_id, state and ready status
            (and result, if the task is successful) which is serialised into
            json and returned.
        """
        task = get_data_async.AsyncResult(task_id)
        if task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'ready': task.ready(),
                'result': task.result
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'ready': task.ready()
            }
        return jsonify(response)
