from flask import Flask
from flask import jsonify, request
from FlaskCelery.flask_celery import make_celery
from SocialTies.socialties import update_all
import json
import requests
import os
flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://redis:6379')
celery = make_celery(flask_app)
PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
TASK_MANAGER_API = 'https://wenet.u-hopper.com/dev/task_manager'
ILOGBASE_API = 'http://streambase1.disi.unitn.it:8096/data/'
COMP_AUTH_KEY = 'zJ9fwKb1CzeJT7zik_2VYpIBc_yclwX4Vd7_lO9sDlo'

@celery.task()
def add_together(a, b):
    print(a+b)
    return {}

@celery.task()
def async_initialize(user_id):
    try:
        new_user = get_profiles_from_profile_manager({'users_IDs': [str(user_id)]})
        print ('Got the profiles')
        offset = 0
        number_of_profiles = 20
        more_profiles_left = True
        while more_profiles_left:
            all_users_test = get_N_profiles_from_profile_manager(offset, number_of_profiles)
            if all_users_test is None:
                more_profiles_left = False
            else:
                relationships = update_all(new_user[0], all_users_test[1:])
                print(relationships)
                add_profiles_to_profile_manager(relationships)
                offset = offset + 20
    except Exception as e:
        print('exception happened!!', e)
    return {}


def get_profiles_from_profile_manager(user_ids):
    entities = []
    print('started the get profiles')
    try:
        for user_id in user_ids['users_IDs']:
            try:
                headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                           'x-wenet-component-apikey': COMP_AUTH_KEY, }
                r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), headers=headers)
                entities.append(r.json())
            except requests.exceptions.HTTPError as e:
                print('Cannot get entity from  Profile manager', e)
        return entities
    except requests.exceptions.HTTPError as e:
        print('Something wrong with user list IDs received from Profile Manager', e)
        return False

def get_N_profiles_from_profile_manager(offset, number_of_profiles):
    entities = []
    try:
        try:
            headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                       'x-wenet-component-apikey': COMP_AUTH_KEY, }
            r = requests.get(PROFILE_MANAGER_API + 'profiles?offset=' + str(offset)+ '&limit=' + str(number_of_profiles), headers=headers)
            entities = r.json().get('profiles')
        except requests.exceptions.HTTPError as e:
            print('Cannot get entity from  Profile manager', e)
        return entities
    except requests.exceptions.HTTPError as e:
        print('Something wrong with user list IDs received from Profile Manager', e)
        return False