from flask import jsonify, make_response
from nba_ws import app


@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': error.description})
