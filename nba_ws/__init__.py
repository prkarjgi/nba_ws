"""NBA-WebService Application Package

Package contents:
    Application factory: create_app

    Subpackages:
        common: Defines helper functions and classes.
        errors: Defines errorhandlers.
        resources: Defines API Resources.

    Modules:
        celery.py: Set-up and config set-up for Celery.
        models.py: Defines of database Models.
        tasks.py: Defines of Celery tasks.
"""
import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)


def create_app(config=os.getenv('APP_SETTINGS')):
    app = Flask(__name__)
    app.config.from_object(config)

    celery.config_from_object(os.getenv('CELERY_CONFIG'))

    db.init_app(app)
    migrate.init_app(app, db)

    from nba_ws.resources import api_bp
    app.register_blueprint(api_bp)

    from nba_ws.errors import errors_bp
    app.register_blueprint(errors_bp)

    return app


from nba_ws import models
