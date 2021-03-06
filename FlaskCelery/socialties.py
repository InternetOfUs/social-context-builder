import json
import math
import requests
import os

##############################
### Similarity Computation ###
##############################
PROFILE_MANAGER_API = os.environ['PROFILE_MANAGER_API']
COMP_AUTH_KEY = os.environ['COMP_AUTH_KEY']

def haversine(theta):
    return (1 - math.cos(theta))/2

def haversine_distance(lon_1, lat_1, lon_2, lat_2):
    try:
        h = haversine(lat_2 - lat_1) + math.cos(lat_1) * math.cos(lat_2) * haversine(lon_2 - lon_1)
        R_earth = 6378100
        if h < 0 or h > 1:
            return 2 * R_earth * math.pi
        return 2 * R_earth * math.asin(math.sqrt(h))
    except:
        pass

def mean_relevant_locations_distance(x, y): # x and y are location lists as described in the current WeNet API.
    try:
        if x == None or y == None or len(x)*len(y) == 0:
            return 1
        mean_distance = 0.0
        max_distance = 0.0
        for loc_x in x:
            for loc_y in y:
                distance = haversine_distance(loc_x['longitude'], loc_x['latitude'], loc_y['longitude'], loc_y['latitude'])
                mean_distance += distance
                if distance > max_distance:
                    max_distance = distance
        print(x, y, max_distance)
        return mean_distance/(len(x) * len(y) * max_distance)
    except:
        pass


def common_planned_activities(x, y): # x and y are planned activities lists as described in the current WeNet API.
    try:
        if x == None or y == None or len(x) * len(y) == 0:
            return 1
        x_attendees = set() #TODO Update it to use some notions of fuzzy membership --- e.g. based on relative frequency of appearance of each attendee.
        y_attendees = set()
        for activity in x:
            x_attendees.update(activity['attendees'])
        for activity in y:
            y_attendees.update(activity['attendees'])
        return len(x_attendees.intersection(y_attendees))/min(len(x_attendees), len(y_attendees))
    except:
        pass

def competences_distance(x, y): # x and y are competences lists as described in the current WeNet API.
    try:
        if x == None or y == None or len(x) * len(y) == 0:
            return 1
        distance = 0.0
        count = 0
        for x_competence in x:
            for y_competence in y:
                if x_competence['name'] == y_competence['name'] and x_competence['ontology'] == y_competence['ontology']:
                    distance += abs(x_competence['level'] - y_competence['level'])
                    count += 1
        return distance/count
    except:
        pass

def meanings_distance(x, y): # x and y are meanings lists as described in the current WeNet API.
    try:
        if x == None or y == None or len(x) * len(y) == 0:
            return 1
        distance = 0.0
        for i in range(5): # Assuming that all profiles contain meanings in the same order!
            distance += (x[i]['level'] - y[i]['level']) ** 2
        return (distance ** 0.5)/(5 ** 0.5)
    except:
        pass


def materials_distance(x, y): # x and y are materials arrays as described in the current WeNet API.
    try:
        distance = 0.0
        if len(x) * len(y) == 0:
            return distance
        for item in x:
            for other_item in y:
                if other_item == item:
                    distance += 1
        return distance / (len(x) * len(y))
    except:
        pass


def similarity(x, y, weights=[1/7]*7): # x, y are users as described in the current WeNet API.
    try:
        similarity_metric = 0.0
        try:
            if x['gender'] == y['gender']:
                similarity_metric += weights[0] * 1
        except:
            pass
        try:
            if x['locale'] == y['locale']:
                similarity_metric += weights[1] * 1
        except:
            pass
        try:
            if x['occupation'] == y['occupation']:
                similarity_metric += weights[2] * 1
        except:
            pass
        try:
            if x.get('relevantLocations') is not None and y.get('relevantLocations') is not None:
                similarity_metric += weights[3] * (1 - mean_relevant_locations_distance(x['relevantLocations'], y['relevantLocations']))
            if x.get('plannedActivities') is not None and y.get('plannedActivities') is not None:
                similarity_metric += weights[4] * (1 - common_planned_activities(x['plannedActivities'], y['plannedActivities']))
            if x.get('competences') is not None and y.get('competences') is not None:
                similarity_metric += weights[5] * (1 - competences_distance(x['competences'], y['competences']))
            if x.get('competences') is not None and y.get('competences') is not None:
                similarity_metric += weights[6] * (1 - meanings_distance(x['meanings'], y['meanings']))
        except:
            pass
        try:
            similarity_metric += weights[3] * (1 - materials_distance(x['materials'], y['materials']))
        except:
            pass

        return similarity_metric
    except:
        pass

def tie_strength_init(new_user, existing_user, all_users):
    try:
        new_similarities = 0.0
        existing_simmilarities = 0.0
        tie_strength = 0.0
        for user in all_users:
            related = get_related_profiles(user)
            if related == None:
                continue
            for relationship in related:
                other_user = relationship['user']
                weight = relationship['weight']
                if weight == None:
                    continue
                # other_user = GET/profiles/{relationship['userId']} #FIXME This needs to be converted to a call to the existing WeNet API.
                new_similarity = similarity(new_user, other_user)
                existing_similarity = similarity(existing_user, user)
                new_similarities += new_similarity
                existing_simmilarities += existing_similarity
                tie_strength += new_similarity * existing_similarity * weight
        if new_similarities * existing_simmilarities == 0:
            return 0.0
        return tie_strength/(new_similarities * existing_simmilarities)
    except:
        pass

def update_all(new_user, all_users):
    try:
        weights = []
        if new_user:
            for user in all_users:
                #weight = tie_strength_init(new_user, user, all_users)
                weights.append({
                    'newUserId': new_user['id'],
                    'existingUserId': user['id'],
                    'weight': 0, #round(weight, 4)
                })
            return weights
        return None
        # returns list of {userID, userID_new, tie_strength}
    except:
        pass

#################
### WeNet API ###
#################

def get_related_profiles(user):
    try:
        """
            {user_id: [profile.json], weight: 0.5}
            """
        try:
            user_ids = []
            weights = []
            try:
                relationships = user['relationships']
            except:
                return None
            if relationships == None:
                return None
            for relationship in relationships:
                user_ids.append(relationship['userId'])
                weights.append(relationship['weight'])
            profiles = get_profiles_from_profile_manager({'users_IDs': user_ids})
            related = []
            for i in range(len(profiles)):
                related.append({
                    'user': profiles[i],
                    'weight': weights[i],
                })
            return related   # returns whole json profile along with weights
        except Exception as e:
            print('Cannot get related relations from  Profile manager', e)
            return None
    except:
        pass

def get_profiles_from_profile_manager(user_ids):
    try:
        entities = []
        try:
            for user_id in user_ids['users_IDs']:
                try:
                    headers = {'connection': 'keep-alive',
                               'x-wenet-component-apikey': COMP_AUTH_KEY, }
                    r = requests.get(PROFILE_MANAGER_API + '/profiles/' + str(user_id), headers=headers)
                    r.raise_for_status()
                    if r.status_code==200:
                        entities.append(r.json())
                except requests.exceptions.HTTPError as e:
                    print('Cannot get entity from  Profile manager', e)
            return entities
        except requests.exceptions.HTTPError as e:
            print('Something wrong with user list IDs received from Profile Manager', e)
            return False
    except:
        pass

if __name__ == '__main__':
    x = range(30)
    user_ids={}
    values=[]
    for n in x:
        values.append(str(n))
    user_ids = {'users_IDs': values }
    # user_ids = {
    #     'users_IDs': ['17', '36', '37', '38', '16'],
    # }
    all_users = get_profiles_from_profile_manager(user_ids)
    output = update_all(all_users[0], all_users[1:])
    print(output)