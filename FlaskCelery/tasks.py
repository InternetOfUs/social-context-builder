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
from datetime import timedelta
import math


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL'])
flask_app.config['CELERYBEAT_SCHEDULE'] = {
    # Executes every minute
    'periodic_task-every-minute': {
        'task': 'periodic_task',
        'schedule': timedelta(hours=int(os.environ['SCHEDULE_IN_HOURS']))
    }
}
celery = make_celery(flask_app)
INTERACTION_PROTOCOL_ENGINE = os.environ['INTERACTION_PROTOCOL_ENGINE']
PROFILE_MANAGER_API = os.environ['PROFILE_MANAGER_API']
TASK_MANAGER_API = os.environ['TASK_MANAGER_API']
COMP_AUTH_KEY = os.environ['COMP_AUTH_KEY']
HUB_API = os.environ['HUB_API']
logging.basicConfig(filename='FlaskCelery/logs/social-context-builder-celery.log', level=logging.INFO, format=f'%(asctime)s Social Context Builder %(levelname)s : %(message)s')
log = logging


@celery.task()
def test_log():
    try:
        log.info('test celery')
    except:
        log.exception('test celery failed')

@celery.task()
def test_2():
    try:
        a = 5 + 5
        return str(a)
    except:
        log.exception('test celery 2 failed')

@celery.task()
def test_3():
    try:
        a = 5 + 5
    except:
        log.exception('test celery 3 failed')

@celery.task(name ="periodic_task")
def periodic_task():
    try:
        return {} #periodic task on pause
        offset = 0
        number_of_profiles = 100
        more_profiles_left = True
        for i in range(600):
            try:
                all_users_in_range = get_N_profiles_from_profile_manager(offset, number_of_profiles)
            except:
                log.info(str(i*20)+' users processed from periodic task')
                break
            if not all_users_in_range:
                log.info(str(i*20)+' users processed from periodic task')
                break
            else:
                for user in all_users_in_range:
                    relationships = user.get('relationships')
                    if relationships:
                        for relationship in relationships:
                            other_weight = relationship.get('weight')
                            if float(other_weight) < 0.1:
                                other_user = relationship.get('userId')
                                try:
                                    other_user = get_profiles_from_profile_manager({'users_IDs': [str(other_user)]})[0]
                                except:
                                    log.info('skipping relation- profile not found' + str(other_user))
                                    continue
                                index = relationships.index(relationship)
                                new_weight = user_similarity.similarity(user, other_user)
                                if 0 <= round(float(new_weight), 4) <= 1:
                                    threshold = 0.05
                                    if (round(float(new_weight), 4) - round((float(other_weight)), 4)) > threshold:
                                        relationship['weight'] = round(float(new_weight), 4)
                                        if not (update_relationship_to_profile_manager(str(user.get('id')), relationship, index)):
                                            log.info('skipping update for'+str(user.get('id')),relationship)
                                            break
                                        try:
                                            log.info('recalculating relationships ' + str(user.get('id')) + ' ' +
                                                     str(relationship.get('userId')) + ' ' + str(round(float(new_weight), 4)))
                                        except:
                                            pass
                offset = offset + 100
        log.info("Period recalculate of relationships finished")
    except Exception:
        log.exception('Daily recalculate failed')
        return {}

@celery.task()
def async_initialize(user_id, app_ids):
    try:
        new_user = get_profiles_from_profile_manager({'users_IDs': [str(user_id)]})[0]
        offset = 0
        number_of_profiles = 50
        relationships = []
        if new_user:
            for i in range(600):
                try:
                    all_users_in_range = get_N_profiles_from_profile_manager(offset, number_of_profiles)
                except:
                    break
                if not all_users_in_range:
                    break
                else:
                    for app_id in app_ids:
                        for user in all_users_in_range:
                            try:
                                if str(user_id) != str(user.get('id')):
                                    new_weight = user_similarity.similarity(new_user, user)
                                    relationships.append({"appId": str(app_id),
                                                          "userId": str(user.get('id')),
                                                          "type": "friend",
                                                          "weight": round(new_weight, 4)})
                                    inverse_relation = {"appId": str(app_id),
                                                          "userId": str(user_id),
                                                          "type": "friend",
                                                          "weight": round(new_weight, 4)}
                                    #set_relationship_to_profile_manager(str(user.get('id')), inverse_relation)
                            except:
                                log.info('exception in building relationships for ' + str(user_id))
                offset = offset + 50
            if relationships:
                patch_profiles_to_profile_manager(user_id, relationships)
            log.info('initialized relationships for user ' + str(user_id))
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
            relationships = get_relationships_from_profile_manager_service(sender_id, appId)
            if relationships:
                for relationship in relationships:
                    if relationship.get('targetId') == receiver_id and relationship.get('appId') == appId:
                        found_relationship = True
                        current_weight = round(float(relationship.get('weight')), 4)
                        new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight, first_total_interaction)
                        log.info(str(current_weight)+'-->'+str(new_weight))
                        threshold = 0.05
                        if (new_weight - current_weight) > threshold and 0 <= new_weight <= 1:
                            relationship = {}
                            relationship['targetId'] = str(receiver_id)
                            relationship['sourceId'] = str(sender_id)
                            relationship['type'] = 'friend'
                            relationship['weight'] = round(float(new_weight), 4)
                            relationship['appId'] = str(appId)
                            log.info('Updating ' + str(sender_id))
                            log.info('Learning', relationship)
                            update_relationship_to_profile_manager_service(relationship)
                            return {}
            try:
                if not found_relationship and appId:
                    current_weight = 0.0
                    new_weight = social_ties_learning.compute_tie_strength(data, type_of_interaction, current_weight,
                                                                           first_total_interaction)
                    update_relationship_to_profile_manager_service({'sourceId': sender_id, 'targetId': receiver_id, 'type': 'friend', 'weight': round(float(new_weight), 4), 'appId': appId})
            except:
                log.exception('Failed to init relation during social_learning for ' + str(sender_id))

    except Exception as e:
        log.exception('Social learning failed for message async_social_ties_learning ')

def get_profiles_from_profile_manager(user_ids):
    entities = []
    try:
        for user_id in user_ids['users_IDs']:
            try:
                headers = {'connection': 'keep-alive',
                           'x-wenet-component-apikey': COMP_AUTH_KEY, }
                r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), headers=headers)
                r.raise_for_status()
                entities.append(r.json())
            except Exception as e:
                log.exception('Cannot get profiles from Profile manager')
        return entities
    except Exception as e:
        log.exception('Invalid user list IDs received', e)
        return False

def get_N_profiles_from_profile_manager(offset, number_of_profiles):
    entities = []
    try:
        try:
            headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                       'x-wenet-component-apikey': COMP_AUTH_KEY, }
            r = requests.get(PROFILE_MANAGER_API + '/profiles?offset=' + str(offset) + '&limit=' + str(number_of_profiles), headers=headers)
            r.raise_for_status()
            entities = r.json().get('profiles')
        except requests.exceptions.HTTPError as e:
            log.exception('Cannot get N entities from  Profile manager')
        return entities
    except Exception as e:
        log.exception('Something wrong with user list IDs received from Profile Manager')
        return False


def patch_profiles_to_profile_manager(user_id, relationships):
    try:
        headers = { 'Content-Type': 'application/json', 'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        data = json.dumps({"relationships": relationships})
        r = requests.patch(PROFILE_MANAGER_API + '/profiles/' + str(user_id), data=data, headers=headers, timeout=60)
        r.raise_for_status()
    except:
        log.exception('except in patch_profiles_to_profile_manager')


def add_profiles_to_profile_manager(relationships, app_ids):
    try:
        headers = { 'Content-Type': 'application/json', 'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        for app_id in app_ids:
            for relationship in relationships:
                if str(relationship['existingUserId']) != str(relationship['newUserId']):
                    data = json.dumps({'userId': str(relationship['existingUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4), 'appId': str(app_id)})
                    try:
                        r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['newUserId']) + '/relationships',
                                         data=data, headers=headers, timeout=60)
                        r.raise_for_status()
                        log.info('POST relationship to ' + str(relationship['newUserId']) )
                        log.info(r.text)
                    except:
                        log.exception(r.text)
                    data = json.dumps({'userId': str(relationship['newUserId']), 'type': 'friend', 'weight': round(float(relationship['weight']),4), 'appId': str(app_id)})
                    try:
                        r = requests.post(PROFILE_MANAGER_API+'/profiles/' + str(relationship['existingUserId']) + '/relationships',
                                         data=data, headers=headers, timeout=60)
                        r.raise_for_status()
                        log.info('POST relationship to ' + str(relationship['existingUserId']) )
                        log.info(r.text)
                    except:
                        log.exception(r.text)
    except Exception as e:
        log.exception('Could not add_profiles_to_profile_manager ')


def get_relationships_from_profile_manager(user_id):
    entities = []
    try:
        try:
            headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                       'x-wenet-component-apikey': COMP_AUTH_KEY, }
            r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships', headers=headers)
            relationships = r.json()
            r.raise_for_status()
            return relationships
        except requests.exceptions.HTTPError as e:
            log.exception('Cannot get relationships from  Profile manager')
        return None
    except requests.exceptions.HTTPError as e:
        log.exception('Something wrong with user list IDs received from Profile Manager')
        return None


def get_relationships_from_profile_manager_service(sourceId, appId):
    entities = []
    try:
        try:
            headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                       'x-wenet-component-apikey': COMP_AUTH_KEY, }
            r = requests.get(PROFILE_MANAGER_API + '/relationships/?sourceId=' + str(sourceId) + '&appId='+appId, headers=headers)
            relationships = r.json()
            r.raise_for_status()
            return relationships.get('relationships')
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
            try:
                r = requests.patch(PROFILE_MANAGER_API + '/profiles/' + str(user_id) + '/relationships/' + str(index), data=data,
                                  headers=headers)
                r.raise_for_status()
                return True
            except:
                log.exception(r.text)
                if 'Timed out' in r.text:
                    log.info('timed out happened')
                    return False
                else:
                    return True
    except requests.exceptions.HTTPError as e:
        log.exception('could not update relationship_to_profile_manager' + str(user_id))


def update_relationship_to_profile_manager_service(relationship):
    try:
        data = json.dumps(relationship)
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY,
                   'Content-Type': 'application/json'}
        if relationship['sourceId']:
            try:
                r = requests.put(PROFILE_MANAGER_API + '/relationships/', data=data,
                                  headers=headers)
                r.raise_for_status()
                return True
            except:
                log.exception(r.text)
                if 'Timed out' in r.text:
                    log.info('timed out happened')
                    return False
                else:
                    return True
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
            r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log.exception('Could not set_relationship_to_profile_manager ' + str(user_id))

def get_first_total_interaction(senderId, receiverID):
    try:
        headers = {'connection': 'keep-alive',
                   'x-wenet-component-apikey': COMP_AUTH_KEY, }
        r = requests.get(INTERACTION_PROTOCOL_ENGINE + '/interactions?senderId=' + str(senderId) + '&receiverId=' + str(receiverID) +
                         '&offset=0', headers=headers)
        r.raise_for_status()
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
            r.raise_for_status()
            return {'first': first_interaction, 'total': total_interactions}
    except Exception as e:
        log.exception('could not calculate get_first_total_interactions' + str(senderId) + ' ' + str(receiverID))


def get_app_ids_for_user(user_id):
    try:
        app_ids = []
        headers = {'Content-Type': 'application/json'}
        url = HUB_API + '/data/user/' + str(user_id) + '/apps'
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        if data:
            for app_id in data:
                app_ids.append(app_id.get('appId'))
        return app_ids
    except:
        log.exception('could not get appids ' + str(user_id))
        return app_ids

