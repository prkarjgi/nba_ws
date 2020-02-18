from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))

db = SQLAlchemy(app=app)

migrate = Migrate(app=app, db=db)

api = Api(app)

import models


class SearchFieldAPI(Resource):
    def __init__(self):
        pass

    def get(self):
        pass

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


api.add_resource(SearchFieldAPI, '/todo/api/search', endpoint='search_field')

db.create_all()

if __name__ == "__main__":
    app.run()
