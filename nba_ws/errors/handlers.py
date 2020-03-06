from flask import jsonify, make_response
from nba_ws.errors import errors_bp


@errors_bp.errorhandler(404)
def not_found(error):
    return jsonify({'message': error.description})
