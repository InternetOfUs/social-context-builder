from flask import Flask
from flask import jsonify, request
from FlaskCelery.flask_celery import make_celery
from FlaskCelery.socialties import update_all
import FlaskCelery.social_ties_learning as social_ties_learning
import FlaskCelery.user_similarity as user_similarity
import json
import requests
import logging
import os


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL'])
celery = make_celery(flask_app)
INTERACTION_PROTOCOL_ENGINE = os.environ['INTERACTION_PROTOCOL_ENGINE']
PROFILE_MANAGER_API = os.environ['PROFILE_MANAGER_API']
TASK_MANAGER_API = os.environ['TASK_MANAGER_API']
COMP_AUTH_KEY = os.environ['COMP_AUTH_KEY']
HUB_API = os.environ['HUB_API']
log = logging.getLogger('FlaskApp')


@celery.task()
def async_initialize(user_id, app_ids):
    try:
        new_user = get_profiles_from_profile_manager({'users_IDs': [str(user_id)]})
        offset = 0
        number_of_profiles = 20
        more_profiles_left = True
        if new_user:
            while more_profiles_left:
                all_users_in_range = get_N_profiles_from_profile_manager(offset, number_of_profiles)
                if all_users_in_range is None:
                    more_profiles_left = False
                else:
                    relationships = update_all(new_user[0], all_users_in_range)
                    if relationships:
                        add_profiles_to_profile_manager(relationships, app_ids)
                    offset = offset + 20
    except Exception as e:
        log.exception('could not initialize relationships for ' + str(user_id), e)
    return {}


@celery.task()
def async_social_ties_profile_update(user_id):
    try:
        new_user = get_profiles_from_profile_manager({'users_IDs': [str(user_id)]})
        if new_user:
            relationships = new_user.get('relationships')
            if relationships:
                for relationship in relationships:
                    other_weight = relationship.get('weight')
                    if float(other_weight) < 0.5:
                        other_user = relationship.get('userId')
                        other_user = get_profiles_from_profile_manager({'users_IDs': [str(other_user)]})
                        index = relationships.index(relationship)
                        new_weight = user_similarity.similarity(new_user, other_user)
                        if 0 <= round(float(new_weight), 4) <= 1:
                            if round(float(new_weight), 4) > round(float(other_weight), 4):
                                relationship['weight'] = round(float(new_weight), 4)
                                update_relationship_to_profile_manager(str(user_id), relationship, index)
    except Exception as e:
        log.exception('could not initialize relationships for ' + str(user_id), e)
    return {}

@celery.task()
def async_social_ties_learning(data):
    try:

        found_relationship = False
        negative_verbs =['reject','report','decline','refuse','ignore']
        type_of_interaction = data['message']['label']
        appId = data['message']['appId']
        if type_of_interaction in ['volunteerForTask','acceptVolunteer','AnsweredPickedMessage','AnsweredQuestionMessage']:
            type_of_interaction = 'positive'
        if any(x in type_of_interaction.lower() for x in negative_verbs):
            type_of_interaction = 'negative'
        sender_id = data['senderId']
        receiver_id = data['message']['receiverId']
        first_total_interaction = get_first_total_interaction(sender_id, receiver_id)
        if type_of_interaction in ['negative', 'positive'] and appId:
            relationships = get_relationships_from_profile_manager(sender_id)
            for relationship in relationships:
                if relationship.get('userId') == receiver_id and relationship.get('appId') == appId:
                    found_relationship = True
                    current_weight = float(relationship.get('weight'))
                    index = relationships.index(relationship)
                    new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight, first_total_interaction)
                    if new_weight != current_weight and new_weight>=0 and new_weight<=1:
                        relationship={}
                        relationship['userId'] = str(receiver_id)
                        relationship['type'] = 'friend'
                        relationship['weight'] = round(float(new_weight), 4)
                        relationship['appId'] = str(appId)
                        update_relationship_to_profile_manager(sender_id, relationship, index)
                        return
            if not found_relationship and appId:
                current_weight = 0.0
                new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight,
                                                                       first_total_interaction)
                set_relationship_to_profile_manager(sender_id, {'userId': receiver_id, 'type': 'friend', 'weight': round(float(new_weight), 4),'appId': appId})

    except Exception as e:
        log.exception('Social learning failed for message async_social_ties_learning ')

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
    except Exception as e:
        log.exception('Something wrong with user list IDs received from Profile Manager', e)
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
            log.exception('Cannot get entity from  Profile manager')
        return entities
    except Exception as e:
        log.exception('Something wrong with user list IDs received from Profile Manager')
        return False


def add_profiles_to_profile_manager(relationships, app_ids):
    try:
        headers = { 'Content-Type': 'application/json', 'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        for app_id in app_ids:
            for relationship in relationships:
                if str(relationship['existingUserId']) != str(relationship['newUserId']):
                    data = json.dumps({'userId': str(relationship['existingUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4), 'appId': str(app_id)})
                    r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['newUserId']) + '/relationships',
                                     data=data, headers=headers)
                    data = json.dumps({'userId': str(relationship['newUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4), 'appId': str(app_id)})
                    r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['existingUserId']) + '/relationships',
                                     data=data, headers=headers)
    except Exception as e:
        log.exception('Could not add_profiles_to_profile_manager from relations initialize for user ')


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
            log.exception('Cannot get relationships from  Profile manager')
        return None
    except requests.exceptions.HTTPError as e:
        log.exception('Something wrong with user list IDs received from Profile Manager')
        return None


def update_relationship_to_profile_manager(user_id, relationship, index):
    try:
        data = json.dumps(relationship)
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY,
                   'Content-Type': 'application/json'}
        if relationship['userId']:
            r = requests.patch(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships/' + str(index), data=data,
                              headers=headers)
    except requests.exceptions.HTTPError as e:
        log.exception('could not update relationship_to_profile_manager' + str(user_id))


def set_relationship_to_profile_manager(user_id, relationship):
    try:
        data = json.dumps(relationship)
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY,
                   'Content-Type': 'application/json'}
        if relationship['userId']:
             r = requests.post(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships', data=data,
                               headers=headers)
    except requests.exceptions.HTTPError as e:
        log.exception('Could not set_relationship_to_profile_manager ' + str(user_id))

def get_first_total_interaction(senderId, receiverID):
    try:
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        r = requests.get(INTERACTION_PROTOCOL_ENGINE + '/interactions?senderId=' + str(senderId) + '&receiverId=' + str(receiverID) +
                         '&offset=0', headers=headers)
        interactions = r.json()
        if interactions.get('total') == 0:
            return {'first': 0, 'last': 0, 'total': 0}
        else:
            total_interactions = interactions.get('total')
            first_interaction = interactions.get('interactions')[0].get('messageTs')
            r = requests.get(
                INTERACTION_PROTOCOL_ENGINE + '/interactions?senderId=' + str(senderId) + '&receiverId=' + str(
                    receiverID) +
                '&offset=' + str(total_interactions - 1), headers=headers)
            return {'first': first_interaction, 'total': total_interactions}
    except requests.exceptions.HTTPError as e:
        log.exception('could not calculate get_first_total_interaction' + str(senderId) + ' ' + str(receiverID))

