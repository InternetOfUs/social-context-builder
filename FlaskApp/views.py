from flask import jsonify, request
from FlaskApp import app, models, db
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
    return 'Wenet Home V3.05'


@app.route("/social/profile/streambase", methods=['POST'])
def social_profile_streambase():
    data = request.json
    print('Received stream - socialprofile', data, flush=True)
    models.SocialProfile().parse(data)
    return {}

@app.route("/social/relations/streambase", methods=['POST'])
def social_relations_streambase():
    data = request.json
    print(data, flush=True)
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
        r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), verify=False)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    try:
        r = requests.get(TASK_MANAGER_API + '/tasks/' + str(task_id), verify=False)
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    if request.method == "POST":
        data = request.json
        return jsonify(data)
    else:
        return 'Need POST request with list of users'


if __name__ == "__main__":
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.run()
