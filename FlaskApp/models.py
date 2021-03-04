from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////db/database.db'
db = SQLAlchemy(app)


class SocialProfile(db.Model):
    userId = db.Column(db.String(80), primary_key=True) #wenetid
    source = db.Column(db.String(50), nullable=False)
    sourceId = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    hometown = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return '<User %r>' % self.userId