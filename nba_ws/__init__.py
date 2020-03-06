from flask import Flask, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from nba_ws.celery import celery
from celery.schedules import crontab
import os


db = SQLAlchemy()
migrate = Migrate()


# from nba_ws.tasks import get_data_async, get_data_periodic
from nba_ws.common.util import TwitterOAuth2
oauth = TwitterOAuth2()

celery.conf.beat_schedule = {
    'get-data-periodic': {
        'task': 'nba_ws.tasks.get_data_periodic',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (oauth.bearer_token,)
    },
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.getenv('APP_SETTINGS'))

    db.init_app(app)
    migrate.init_app(app, db)

    from nba_ws.resources import api_bp
    app.register_blueprint(api_bp)

    return app


from nba_ws import models
