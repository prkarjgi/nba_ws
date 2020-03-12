"""Contains API Resources used for performing CRUD operations on search fields.

Search fields contain the information used to perform a Twitter search request
such as: the query string, filters, max_id, since_id, etc. The search fields
are stored in the SearchField model.
This module contains classes used to perform CRUD operations on search fields:
    SearchFieldAPI
    SearchFieldListAPI
"""
import json

from flask import abort, jsonify
from flask_restful import Resource, marshal, reqparse

from nba_ws import db
from nba_ws.common.util import clean_search_field, sf_format
from nba_ws.models import SearchField


class SearchFieldAPI(Resource):
    """This API is used to Read, Update or Delete an existing Search Field.

    HTTP Methods supported: GET, PUT, DELETE.

    Attributes:
        reqparse: instance of the reqparse.RequestParser class used to validate
            data parameters passed in the request.
    """
    def __init__(self):
        """Creates attributes and inits Resource class constructor.

        Arguments added to reqparse:
            search_field
        """
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldAPI, self).__init__()

    def get(self, search_id):
        """Returns data of Search Field specified by the search_id argument.

        Args:
            search_id: integer used as an id for a Search Field.

        Returns:
            A dictionary containing Search Field data formatted according to
            the sf_format object (see sf_format from nba_ws.common.util for
            more details).

        Raises:
            HTTPError: if no Search Field with the given search_id is found.
        """
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
        """Updates the Search Field specified by the search_id argument.

        Args:
            search_id: integer used as an id for a search field.

        Returns:
            HTTP status code 200 if request is completed.

        Raises:
            HTTPError: if search_field argument is not passed in request
                or if no Search Field with the given search_id is found.
        """
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
        """Deletes the Search Field specified by the search_id argument.

        Args:
            search_id: integer used as an id for a search field.

        Returns:
            HTTP status code 200 if request is completed.

        Raises:
            HTTPError: if no Search Field with the given search_id is found.
        """
        search_field = SearchField.query.filter_by(id=search_id).first()
        if not search_field:
            abort(404, description='Not found')
        db.session.delete(search_field)
        db.session.commit()
        return 200


class SearchFieldListAPI(Resource):
    """Reads multiple Search Fields or Creates new Search Fields.

    HTTP Methods supported: GET, POST.

    Attributes:
        reqparse: instance of the reqparse.RequestParser class used to validate
            data parameters passed in the request.
    """
    def __init__(self):
        """Creates attributes and runs Resource class constructor.

        Arguments added to reqparse:
            search_field
        """
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'search_field',
            type=dict,
            location='json'
        )
        super(SearchFieldListAPI, self).__init__()

    def get(self):
        """Returns all the Search Fields stored in the SearchField model.

        Returns:
            Returns a json serialized dictionary containing the Search Fields
            formatted according to the clean_search_field object (see
            clean_search_field from nba_ws.common.util for more details).
        """
        search_fields = SearchField.query.order_by(SearchField.id.desc()).all()
        formatted_sf = [
            marshal(clean_search_field(sf), sf_format) for sf in search_fields
        ]
        return jsonify({'search_fields': formatted_sf})

    def post(self):
        """Adds a new Search Field specified by the search_field request arg.

        Returns:
            Returns a dictionary containing data of the new Search Field added
            formatted according to the sf_format object
            (see sf_format from nba_ws.common.util for more details) and
            HTTP response code 201.

        Raises:
            HTTPError: If the argument 'search_field' is not passed in the
                request.
        """
        args = self.reqparse.parse_args()
        if not args['search_field']:
            abort(404, description="\'search_field\' is a necessary argument.")
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
