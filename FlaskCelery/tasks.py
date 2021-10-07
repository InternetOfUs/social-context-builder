from flask import Flask
from flask import jsonify, request
from FlaskCelery.flask_celery import make_celery
from FlaskCelery.socialties import update_all
import FlaskCelery.social_ties_learning as social_ties_learning
import json
import requests
import logging


import os
flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://redis:6379')
celery = make_celery(flask_app)
PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
TASK_MANAGER_API = 'https://wenet.u-hopper.com/dev/task_manager'
ILOGBASE_API = 'http://streambase1.disi.unitn.it:8096/data/'
INTERACTION_PROTOCOL_ENGINE = 'https://wenet.u-hopper.com/dev/interaction_protocol_engine'
COMP_AUTH_KEY = 'zJ9fwKb1CzeJT7zik_2VYpIBc_yclwX4Vd7_lO9sDlo'
log = logging.getLogger('FlaskApp')
log.info('Task celery logging initiated')
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
        log.exception('could not initialize relationships for ' + str(user_id), e)
    return {}

@celery.task()
def async_social_ties_learning(data):

    try:
        raise Exception
        found_relationship = False
        negative_verbs =['reject','report','decline','refuse','ignore']
        type_of_interaction = data['message']['label']
        if type_of_interaction in ['volunteerForTask','acceptVolunteer','AnsweredPickedMessage','AnsweredQuestionMessage']:
            type_of_interaction = 'positive'
        if any(x in type_of_interaction.lower() for x in negative_verbs):
            type_of_interaction = 'negative'
        sender_id = data['senderId']
        receiver_id = data['message']['receiverId']
        first_total_interaction = get_first_total_interaction(sender_id, receiver_id)
        if type_of_interaction in ['negative', 'positive']:
            relationships = get_relationships_from_profile_manager(sender_id)
            print(relationships)
            for relationship in relationships:
                if relationship.get('userId') == receiver_id:
                    found_relationship = True
                    current_weight = float(relationship.get('weight'))
                    index = relationships.index(relationship)
                    new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight, first_total_interaction)
                    print('new weight')
                    print(new_weight)
                    if new_weight != current_weight and new_weight>=0 and new_weight<=1:
                        relationship={}
                        relationship['userId'] = receiver_id
                        relationship['type'] = 'friend'
                        relationship['weight'] = round(float(new_weight), 4)
                        update_relationship_to_profile_manager(sender_id, relationship, index)
                        return
            if not found_relationship:
                current_weight = 0.0
                new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight,
                                                                       first_total_interaction)
                set_relationship_to_profile_manager(sender_id, {'userId': receiver_id, 'type': 'friend', 'weight': round(float(new_weight), 4)})

    except Exception as e:
        log.exception('Social learning failed for message : %s', data)


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
            ranking_already_in_db = FlaskApp.models.DiversityRanking.query.filter((DiversityRanking.userId == new_ranking.userId) &
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
            FlaskApp.db.session.commit()
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
            r = requests.get(PROFILE_MANAGER_API + '/profiles?offset=' + str(offset) + '&limit=' + str(number_of_profiles), headers=headers)
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
                data = json.dumps({'userId': str(relationship['existingUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4)})
                print(data)
                r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['newUserId']) + '/relationships',
                                 data=data, headers=headers)
                data = json.dumps({'userId': str(relationship['newUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4)})
                r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['existingUserId']) + '/relationships',
                                 data=data, headers=headers)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')


def get_relationships_from_profile_manager(user_id):
    entities = []
    try:
        try:
            headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                       'x-wenet-component-apikey': COMP_AUTH_KEY, }
            r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships', headers=headers)
            relationships = r.json()
            return relationships
        except requests.exceptions.HTTPError as e:
            print('Cannot get relationships from  Profile manager', e)
        return None
    except requests.exceptions.HTTPError as e:
        print('Something wrong with user list IDs received from Profile Manager', e)
        return None


def update_relationship_to_profile_manager(user_id, relationship, index):
    try:
        data = json.dumps(relationship)
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY,
                   'Content-Type': 'application/json'}
        if relationship['userId']:
            r = requests.patch(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships/'+ str(index), data=data,
                              headers=headers)
    except requests.exceptions.HTTPError as e:
        print('exception')

def set_relationship_to_profile_manager(user_id, relationship):
    try:
        data = json.dumps(relationship)
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY,
                   'Content-Type': 'application/json'}
        if relationship['userId']:
            r = requests.post(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships', data=data,
                              headers=headers)
            print(r.status_code)
    except requests.exceptions.HTTPError as e:
        print('exception')

def get_first_total_interaction(senderId, receiverID):
    try:
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        r = requests.get(INTERACTION_PROTOCOL_ENGINE + '/interactions?senderId=' + str(senderId) + '&receiverId=' + str(receiverID) +
                         '&offset=0', headers=headers)
        interactions = r.json()
        print(r.status_code)
        print(interactions)
        if interactions.get('total') == 0:
            print('total=0')
            return {'first': 0, 'last': 0, 'total': 0}
        else:
            total_interactions = interactions.get('total')
            first_interaction = interactions.get('interactions')[0].get('messageTs')
            r = requests.get(
                INTERACTION_PROTOCOL_ENGINE + '/interactions?senderId=' + str(senderId) + '&receiverId=' + str(
                    receiverID) +
                '&offset=' + str(total_interactions - 1), headers=headers)
            print(first_interaction, total_interactions)
            return {'first': first_interaction, 'total': total_interactions}
    except requests.exceptions.HTTPError as e:
        print('could not calculate interaction', e)
