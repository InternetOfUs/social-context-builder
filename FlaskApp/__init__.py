from flask import Flask
app = Flask(__name__)
from FlaskApp import views
from .models import db
db.create_all()