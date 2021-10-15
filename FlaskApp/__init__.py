from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/database.db'
app.config['CELERY_BROKER_URL'] = os.environ['CELERY_BROKER_URL']
logging.basicConfig(filename='FlaskApp/logs/social_context_builder.log', level=logging.INFO, format=f'%(asctime)s Social Context Builder %(levelname)s : %(message)s')
db = SQLAlchemy(app)
from FlaskApp import views
db.create_all()

