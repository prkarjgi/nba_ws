from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


db = SQLAlchemy()
migrate = Migrate()


def create_app(config=os.getenv('APP_SETTINGS')):
    app = Flask(__name__)
    app.config.from_object(config)
    # print(app.config.items())

    db.init_app(app)
    migrate.init_app(app, db)

    from nba_ws.resources import api_bp
    app.register_blueprint(api_bp)

    from nba_ws.errors import errors_bp
    app.register_blueprint(errors_bp)

    return app


from nba_ws import models
