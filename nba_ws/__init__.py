from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

from nba_ws import models, routes

db.create_all()
