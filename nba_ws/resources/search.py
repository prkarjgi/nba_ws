from flask import abort, jsonify
from flask_restful import Resource, marshal, reqparse
from nba_ws import db, celery
from nba_ws.models import SearchField
from nba_ws.tasks import get_data_async
from nba_ws.common.util import TwitterOAuth2, status_format,\
    sf_format, clean_search_field
import json


class SearchFieldAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldAPI, self).__init__()

    def get(self, search_id):
        search_field = SearchField.query.filter_by(
            id=search_id
        ).first()
        if not search_field:
            abort(404, description='Not found')
        resp = {}
        resp['search_field'] = json.loads(search_field.search_field)
        resp['author'] = search_field.author
        resp['datetime_added'] = search_field.datetime_added
        resp['search_id'] = search_id
        return {'sf': marshal(resp, sf_format)}

    def put(self, search_id):
        args = self.reqparse.parse_args()
        if not args['search_field']:
            abort(404, description='\'search_field\' is a necessary parameter')
        search_field = SearchField.query.filter_by(id=search_id).first()
        if not search_field:
            abort(404, description='Not found')
        search_field.search_field = json.dumps(args['search_field'])
        search_field.author = args['search_field']['q']['author']
        db.session.add(search_field)
        db.session.commit()
        return 200

    def delete(self, search_id):
        search_field = SearchField.query.filter_by(id=search_id).first()
        if not search_field:
            abort(404, description='Not found')
        db.session.delete(search_field)
        db.session.commit()
        return 200


class SearchFieldListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldListAPI, self).__init__()

    def get(self):
        search_fields = SearchField.query.order_by(SearchField.id.desc()).all()
        formatted_sf = [
            marshal(clean_search_field(sf), sf_format) for sf in search_fields
        ]
        return jsonify({'search_fields': formatted_sf})

    def post(self):
        args = self.reqparse.parse_args()
        sf = args['search_field']
        search_field = SearchField(json.dumps(sf), sf['q']['author'])
        db.session.add(search_field)
        db.session.commit()
        resp = {}
        resp['search_field'] = json.dumps(sf)
        resp['author'] = args['search_field']['q']['author']
        resp['datetime_added'] = search_field.datetime_added
        resp['search_id'] = search_field.id
        return {'sf': marshal(resp, sf_format)}, 201


class SearchTriggerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(SearchTriggerAPI, self).__init__()

    def get(self):
        bearer_token = TwitterOAuth2().bearer_token
        result = get_data_async.delay(bearer_token)
        task = {
            'task_id': result.id
        }
        return jsonify({
            'task_details': marshal(task, status_format)
        })


class TaskStatusAPI(Resource):
    def __init__(self):
        super(TaskStatusAPI, self).__init__()

    def get(self, task_id):
        task = get_data_async.AsyncResult(task_id)
        if task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'ready': task.ready(),
                'result': task.result
            }
        else:
            response = {
                'state': task.state,
                'ready': task.ready()
            }
        return jsonify(response)
