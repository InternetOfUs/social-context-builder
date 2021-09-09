from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/database.db'
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379'
db = SQLAlchemy(app)
from FlaskApp import views
db.create_all()

