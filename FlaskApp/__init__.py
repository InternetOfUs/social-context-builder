from flask import Flask
app = Flask(__name__)
from FlaskApp import views, models
models.db.create_all()