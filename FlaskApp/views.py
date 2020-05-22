from flask import jsonify, request
from FlaskApp import app
import random
import csv
import json
import requests

PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
TASK_MANAGER_API = 'https://wenet.u-hopper.com/dev/task_manager'
ILOGBASE_API = 'http://streambase1.disi.unitn.it:8096/data/'

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
    return 'Wenet Home'


@app.route("/social/relations/<user_id>", methods=['GET'])
def show_social_relations(user_id):
    try:
        try:
            r = requests.put(PROFILE_MANAGER_API+'/profiles/' + str(user_id),
                             json={'relationships': [{'userId': '1', 'type': 'friend'}]})
        except requests.exceptions.HTTPError as e:
            print('Issue with Profile manager')
        try:
            headers = {'Authorization': 'test:testtoken'}
            r = requests.get(ILOGBASE_API + str(user_id)+ '?experimentId=testtest&from=20200301&to=20200312&properties=tasksanswers', headers=headers)
        except requests.exceptions.HTTPError as e:
            print('Issue with ILOGBASE ')
        try:
            r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id))
            return jsonify(r.json()['relationships'])
        except requests.exceptions.HTTPError as e:
            print('Issue with Profile manager')
        return 'couldnt get relationships'
        # else:
        #     return 'Not found!'
    except requests.exceptions.HTTPError as e:
        print(e.response.text)


@app.route("/social/explanations/<user_id>/<task_id>/", methods=['GET'])
def show_social_explanations(user_id, task_id):
    explanation = {"Summary":{"Explanation":{"Context":["relevant(development)"],"Facts":["worksOn(development, bob"],
                                             "Triggered rules":{"R1":"worksOn(X,Y) AND relevant(X)IMPLIES suggest(Y)"}}},
                   "description":"Social Explanation"}
    try:
        r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id))
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    try:
        r = requests.get(TASK_MANAGER_API + '/tasks/' + str(task_id))
    except requests.exceptions.HTTPError as e:
        print(e.response.text)
    return jsonify(explanation)


@app.route("/social/preferences/<user_id>/<task_id>/", methods=['GET','POST'])
def show_social_preferences(user_id, task_id):
    try:
        r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id))
    except requests.exceptions.HTTPError as e:
        print('Issue with Profile manager')
    try:
        r = requests.get(TASK_MANAGER_API + '/tasks/' + str(task_id))
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