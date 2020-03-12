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


db = SQLAlchemy()
migrate = Migrate()


def create_app(config=os.getenv('APP_SETTINGS')):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)

    from nba_ws.resources import api_bp
    app.register_blueprint(api_bp)

    from nba_ws.errors import errors_bp
    app.register_blueprint(errors_bp)

    return app


from nba_ws import models
