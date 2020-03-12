"""This subpackage is used to handle errors produced by the application.
"""
from flask import Blueprint

errors_bp = Blueprint('errors', __name__)

from nba_ws.errors import handlers
