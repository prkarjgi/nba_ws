from flask import Flask
import os

app = Flask(__name__)
app.config.from_object(os.getenv('APP_SETTINGS'))


@app.route('/')
@app.route('/index')
def index():
    return 'Hello'
