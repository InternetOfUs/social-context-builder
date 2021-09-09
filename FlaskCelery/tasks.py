from flask import Flask

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379')
celery = make_celery(flask_app)

@celery.task()
def add_together(a, b):
    return a + b