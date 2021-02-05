from flask import jsonify, request
from FlaskApp import app
import random
import csv
import json
import requests

PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
TASK_MANAGER_API = 'https://wenet.u-hopper.com/dev/task_manager'
ILOGBASE_API = 'http://streambase1.disi.unitn.it:8096/data/'
COMP_AUTH_KEY = 'zJ9fwKb1CzeJT7zik_2VYpIBc_yclwX4Vd7_lO9sDlo'



class User(object):
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


class SocialRelation(object):
    def __init__(self, user_id, friend_id, relation_type, weight, source):
        self.user_id, self.friend_id = user_id, friend_id
        self.relation_type, self.weight = relation_type, weight
        self.source = source

    def __str__(self):
        return '%s %s %s' % (self.user_id, self.friend_id, self.relation_type)


class Task(object):
    def __init__(self,task_id, user_id, description):
        self.task_id, self.user_id, self.description =task_id, user_id, description



@app.route("/")
def home():
    return 'Wenet Home V2.00'


@app.route("/social/relations/<user_id>", methods=['GET'])
def show_social_relations(user_id):
    try:
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
