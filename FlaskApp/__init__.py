from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/database.db'
db = SQLAlchemy(app)
from FlaskApp import views
db.create_all()

