from flask import jsonify, request
from FlaskApp import app, models, db
from Ranking.ranking import parser, rank_entities, file_parser, order_answers
from FlaskCelery.tasks import async_initialize, add_together
from FlaskCelery.ranking_learning import ranking_model
import json
import requests
import os

PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
TASK_MANAGER_API = 'https://wenet.u-hopper.com/dev/task_manager'
ILOGBASE_API = 'http://streambase1.disi.unitn.it:8096/data/'
COMP_AUTH_KEY = 'zJ9fwKb1CzeJT7zik_2VYpIBc_yclwX4Vd7_lO9sDlo'
#COMP_AUTH_KEY = os.environ['COMP_AUTH_KEY']



@app.route("/")
def home():
    return 'Wenet Home V3.08'


@app.route("/social/profile/streambase", methods=['POST'])
def social_profile_streambase():
    data = request.json
    print('Received stream - socialprofile', data, flush=True)
    models.SocialProfile().parse(data)
    return {}

@app.route("/social/relations/streambase", methods=['POST'])
def social_relations_streambase():
    data = request.json
    print('Received sream - Social relation', data, flush=True)
    models.SocialRelations().parse(data)
    temp = models.SocialRelations()
    try:
        temp.weigh_social_relations(data['socialrelations']['userId'])

    except Exception as e:
        app.logger.info('exception', data, e)

    return {}


@app.route("/social/relations/all", methods=['GET'])
def social_relations_all():
    sr = models.SocialRelations.query.order_by(models.SocialRelations.userId).all()
    sr_out = []
    for profile in sr:
        sr_out.append({'name': profile.__dict__['userId'], 'id': profile.__dict__['userDestinationId']})
    return jsonify(sr_out)


@app.route("/social/profile/all", methods=['GET'])
def social_profiles_all():
    sp = models.SocialProfile.query.order_by(models.SocialProfile.userId).all()
    sp_out = []
    for profile in sp:
        sp_out.append({'name': profile.__dict__['userId'], 'id': profile.__dict__['sourceId']})
    return jsonify(sp_out)


@app.route("/social/relations/initialize/<user_id>", methods=['POST'])
def initialize_social_relations(user_id):
    result = async_initialize.delay(user_id)
    return {}


@app.route("/social/relations/initialize/test/<user_id>", methods=['POST'])
def initialize_social_relations_test(user_id):
    # x = range(30)
    # user_ids={}
    # values=[]
    # for n in x:
    #     values.append(str(n))
    # user_ids = {'users_IDs': values }
    # all_users = get_profiles_from_profile_manager(user_ids)
    # print("******user######")
    # print("******user######")
    # print(all_users[0])
    # print('^^^^^^^^^^^^')
    # print(all_users[1:])
    # relationships = update_all(all_users[0], all_users[1:])
    # add_profiles_to_profile_manager(relationships)
    result = add_together.delay(23, 42)
    return {}
@app.route("/social/relations/<user_id>", methods=['GET', 'POST'])
def show_social_relations(user_id):
    try:
        if request.method == 'POST':
            print(request.json)
        data = json.dumps({'relationships': [{'userId': '1', 'type': 'friend'}]})
        r = requests.put(PROFILE_MANAGER_API+'/profiles/' + str(user_id),
                         json=data, verify=False)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    try:
        headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive', 'x-wenet-component-apikey': COMP_AUTH_KEY, }
        url = ILOGBASE_API + str(user_id) + '?experimentId=wenetTest&from=20200521&to=20200521&properties=socialrelations'
        r = requests.get(url, headers=headers, verify=False)
    except requests.Timeout as err:
        print('TIMEOUT ', err)
    except requests.RequestException as err:
        print(err)
    try:
        headers = {
            'content-type': "application/json",
            'x-wenet-component-apikey': COMP_AUTH_KEY,
        }

        r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), headers=headers, verify=False, timeout=1)
        relationships = r.json().get('relationships')
        if relationships:
            return jsonify(relationships)
        else:
            return 'no relationships'
    except KeyError as e:
        return 'no relationships exist'
    except Exception as e:
        return 'no relationships found'
    return 'couldnt get relationships'


@app.route("/social/explanations/<user_id>/<task_id>/", methods=['GET'])
def show_social_explanations(user_id, task_id):
    explanation = {"Summary":{"Explanation":{"Context":["relevant(development)"],"Facts":["worksOn(development, bob"],
                                             "Triggered rules":{"R1":"worksOn(X,Y) AND relevant(X)IMPLIES suggest(Y)"}}},
                   "description":"Social Explanation"}
    try:
        r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), verify=False)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    try:
        r = requests.get(TASK_MANAGER_API + '/tasks/' + str(task_id), verify=False)
    except requests.exceptions.HTTPError as e:
        print(e.response.text)
    return jsonify(explanation)


@app.route("/social/preferences/<user_id>/<task_id>/", methods=['GET','POST'])
def show_social_preferences(user_id, task_id):
    try:
        if request.method == "POST":
            print('post method')
            return jsonify({"users_IDs": rank_profiles(request.json)})
        else:
            return jsonify(request.json)
    except requests.exceptions.HTTPError as e:
        print('Exception social preferences, returning not ranked user list', e)
        return jsonify(request.json)

@app.route("/social/preferences/answers/<user_id>/<task_id>/", methods=['POST'])
def show_social_preferences_answer(user_id, task_id):
    try:
        data={}
        data['users_IDs']=[]
        answers = {}
        if request.method == "POST":
            print(request.json)
            
            for answer in request.json['data']:
                data['users_IDs'].append(answer['userId'])
                answers[answer['userId']] = answer['answer']
            ranked_users = rank_profiles(data)

            return jsonify(order_answers(answers, ranked_users))
        else:
            return jsonify(request.json)
    except requests.exceptions.HTTPError as e:
        print('Exception social preferences, returning not ranked user list', e)
        return jsonify(request.json)


@app.route("/social/preferences/answers/<user_id>/<task_id>/<selection>/update", methods=['PUT'])
def show_social_preferences_selection(user_id, task_id, selection):
    if request.method == "PUT":
        user_ids = []
        for answer in request.json():
            user_ids.append(answer['userId'])
        suggested_entities = get_profiles_from_profile_manager(user_ids)
    user_preference = selection #dummy, as for now
    model = ranking_model(user_preference, suggested_entities)
    print(model)

def rank_profiles(user_ids):
    MODEL = [0.5] * 5
    DIVERSITY_COEFFICIENT = 0.4
    profiles = get_profiles_from_profile_manager(user_ids)
    if profiles:
        dict_of_entities = parser(profiles)
        ranked = rank_entities(dict_of_entities, MODEL, DIVERSITY_COEFFICIENT)
        return ranked
    else:
        print('Could not get profiles')
        return False

def get_profiles_from_profile_manager(user_ids):
    entities = []
    try:
        for user_id in user_ids['users_IDs']:
            try:
                headers = {'Authorization': 'test:wenet', 'connection': 'keep-alive',
                           'x-wenet-component-apikey': COMP_AUTH_KEY, }
                r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), headers=headers)
                if r.status_code == 200:
                    entities.append(r.json())
            except requests.exceptions.HTTPError as e:
                print('Cannot get entity from  Profile manager', e)
        return entities
    except requests.exceptions.HTTPError as e:
        print('Something wrong with user list IDs received from Profile Manager', e)
        return False


if __name__ == "__main__":
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.run()
