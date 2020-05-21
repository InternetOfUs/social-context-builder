from flask import jsonify, request
from FlaskApp import app
import random
import csv
import json
import requests

PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'

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


def import_users():
    users = []
    try:
        for i in range(1, 5):
            r = requests.get(PROFILE_MANAGER_API+'/profiles/' + str(i))
            users.append(User(user_id=r.json()['id'], name=r.json()['name']))
    except Exception as e:
        return 'Did not get user!'+ e
    return users


def import_tasks():
    tasks = []
    tasks.append(Task(task_id='5eb90acc7b39534433cc00e9', user_id='', description='Lets Have dinner'))
    return tasks


def build_relation_data():
    users = import_users()
    social_relations = []
    relation_types = ['family', 'friend', 'contact', 'colleague', 'other']
    sources = ['Facebook', 'LinkedIn', 'Instagram']
    for i in range(random.randint(50, 80)):
        weight = round(random.uniform(0.0, 1.0), 1)
        user, friend = random.choice(users), random.choice(users)
        type, source_id = random.choice(relation_types),random.choice(sources)
        if user.user_id != friend.user_id:
            social_relations.append(SocialRelation(user.user_id, friend.user_id,
                                                   type, weight, source_id))
    return social_relations


def rank_users_for_task_classifier():
    tasks = import_tasks()
    users = import_users()
    ranked_users_for_task = {}
    for task in tasks:
        ranked_users_for_task[task.task_id] = {'description': 'Ordered list of User IDs',
                                               'schema': {'type': 'array',
                                                          'items': [user.user_id for user in
                                                                    random.sample(users, random.randint(2, 4))]}}
    return ranked_users_for_task


social_relations = build_relation_data()
ranked_users_for_task = rank_users_for_task_classifier()


@app.route("/")
def home():
    return 'Wenet Home'


@app.route("/social/relations/<user_id>", methods=['GET'])
def show_social_relations(user_id):
    try:
        user_social_relations = {user_id: {'description': 'User Relations',
                                               'schema': {'type': 'array',
                                                          'items': [sr.__dict__ for sr in social_relations
                                                                    if user_id == sr.user_id]
                                                          }
                                           }
                                 }
        if user_social_relations[user_id]['schema']['items']:
            r = requests.put(PROFILE_MANAGER_API+'/profiles/' + str(user_id),
                             json={'relationships': [{'userId': '1', 'type': 'friend'}]})
            return jsonify(user_social_relations[user_id])
        else:
            return 'Not found!'
    except Exception as e:
        return 'Not found!'


@app.route("/social/explanations/<user_id>/<task_id>/", methods=['GET'])
def show_social_explanations(user_id, task_id):
    explanation = {"Summary":{"Explanation":{"Context":["relevant(development)"],"Facts":["worksOn(development, bob"],
                                             "Triggered rules":{"R1":"worksOn(X,Y) AND relevant(X)IMPLIES suggest(Y)"}}},
                   "description":"Social Explanation"}
    return jsonify(explanation)


@app.route("/social/preferences/<user_id>/<task_id>/", methods=['GET','POST'])
def show_social_preferences(user_id, task_id):
    task_id ='5eb90acc7b39534433cc00e9'
    if request.method == "POST":
        data = request.json
        return jsonify(data)
    else:
        try:
            if ranked_users_for_task[task_id]:
                return jsonify(ranked_users_for_task[task_id])
            else:
                return 'Not found!'
        except Exception as e:
            return 'Not found!'


if __name__ == "__main__":
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.run()