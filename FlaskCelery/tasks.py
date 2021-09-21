from flask import Flask
from flask import jsonify, request
from FlaskCelery.flask_celery import make_celery
from FlaskCelery.socialties import update_all
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
        if new_user:
            while more_profiles_left:
                print('into the while clause')
                all_users_in_range = get_N_profiles_from_profile_manager(offset, number_of_profiles)
                print ('got N profiles')
                if all_users_in_range is None:
                    more_profiles_left = False
                else:
                    print ('going to update relations')
                    relationships = update_all(new_user[0], all_users_in_range)
                    if relationships:
                        add_profiles_to_profile_manager(relationships)
                        print ('PROFILES ADDED')
                    offset = offset + 20
    except Exception as e:
        print('exception happened!!', e)
    return {}


@celery.task()
def async_ranking_learning(user_id, new_model, task_id):
    try:
        new_ranking = DiversityRanking(userId=user_id,
                                       taskId=task_id,
                                       openess=round(new_model[0],4),
                                       consientiousness=round(new_model[1],4),
                                       extraversion=round(new_model[2],4),
                                       agreeableness=round(new_model[3],4),
                                       neuroticism=round(new_model[4],4),
                                       ts=int(time.time() * 1000))
        try:
            ranking_already_in_db = DiversityRanking.query.filter((DiversityRanking.userId == new_ranking.userId) &
                                                                  (DiversityRanking.taskId == new_ranking.taskId)).first()
            if not ranking_already_in_db:

                db.session.add(new_ranking)
            else: #update ranking
                ranking_already_in_db.openess=new_ranking.openess
                ranking_already_in_db.consientiousness = new_ranking.consientiousness
                ranking_already_in_db.extraversion = new_ranking.extraversion
                ranking_already_in_db.agreeableness = new_ranking.agreeableness
                ranking_already_in_db.neuroticism = new_ranking.neuroticism
                ranking_already_in_db.ts = new_ranking.ts
        except Exception as error:
            print('exception while trying to query ranking from DB ', error)
        db.session.commit()
    except Exception as error:
        print('exception , could not add ranking to DB for user ' + str(user_id), error )
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
    
def add_profiles_to_profile_manager(relationships):
    # [{
    #     newUserId: "123",
    #     existingUserId: "456",
    #     weight: 0.49,
    # }]
    try:
        print ('got into add profiles')
        headers = { 'Content-Type': 'application/json', 'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        for relationship in relationships:
            if str(relationship['existingUserId']) != str(relationship['newUserId']):
                data = json.dumps({'userId': str(relationship['existingUserId']), 'type': 'friend', 'weight': relationship['weight']})
                print(data)
                r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['newUserId']) + '/relationships',
                                 data=data, headers=headers)
                data = json.dumps({'userId': str(relationship['newUserId']), 'type': 'friend', 'weight': relationship['weight']})
                r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['existingUserId']) + '/relationships',
                                 data=data, headers=headers)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
