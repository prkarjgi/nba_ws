from flask import Blueprint

errors_bp = Blueprint('errors', __name__)

from nba_ws.errors import handlers
