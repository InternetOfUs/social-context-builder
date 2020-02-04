from flask import jsonify
from FlaskApp import app
import random
import csv
import json


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
    with open('FlaskApp/data/users.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            users.append(User(user_id=row[0], name=row[1]))
    return users


def import_tasks():
    tasks = []
    with open('FlaskApp/data/tasks.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            tasks.append(Task(task_id=row[0], user_id='', description=row[1]))
    return tasks


def build_relation_data():
    users = import_users()
    social_relations = []
    relation_types = ['family', 'friend', 'contact', 'colleague', 'other']
    sources = ['Facebook', 'LinkedIn', 'Instagram']
    for i in range(random.randint(300, 500)):
        weight = round(random.uniform(0.0, 1.0), 1)
        user, friend = random.choice(users), random.choice(users)
        relation_type, source_id = random.choice(relation_types),random.choice(sources)
        if user != friend:
            social_relations.append(SocialRelation(user.user_id, friend.user_id,
                                                   relation_type, weight, source_id))
    return social_relations


def match_user_for_task_classifier():
    tasks = import_tasks()
    matched_users_for_task = {}
    with open('FlaskApp/data/rules.txt') as json_file:
        rules = json.load(json_file)
    for task in tasks:
        matched_users_for_task[task.task_id] = {'description': 'Social Explanation',
                                                'Summary': random.choice(rules)}
    return matched_users_for_task


def rank_users_for_task_classifier():
    tasks = import_tasks()
    users = import_users()
    ranked_users_for_task = {}
    for task in tasks:
        ranked_users_for_task[task.task_id] = {'description': 'Ordered list of User IDs',
                                               'schema': {'type': 'array',
                                                          'items': [user.user_id for user in
                                                                    random.sample(users, random.randint(2, 20))]}}
    return ranked_users_for_task


social_relations = build_relation_data()
matched_users_for_task = match_user_for_task_classifier()
ranked_users_for_task = rank_users_for_task_classifier()


@app.route("/")
def hello():
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
            return jsonify(user_social_relations[user_id])
        else:
            return 'Not found!'
    except Exception as e:
        return 'Not found!'


@app.route("/social/explanations/<user_id>/<task_id>/", methods=['GET'])
def show_social_explanations(user_id, task_id):
    try:
        if matched_users_for_task[task_id]:
            return jsonify(matched_users_for_task[task_id])
        else:
            return 'Not found!'
    except Exception as e:
        return 'Not found!'


@app.route("/social/preferences/<user_id>/<task_id>/", methods=['GET'])
def show_social_preferences(user_id, task_id):
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