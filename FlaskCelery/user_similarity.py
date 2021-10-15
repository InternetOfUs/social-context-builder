import json
import math

##############################
### Similarity Computation ###
##############################

def haversine(theta):
    try:
        return (1 - math.cos(theta))/2
    except:
        pass


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


def similarity(x, y, weights=[1/7]*7): # x, y are users as described in the current WeNet API.
    try:
        similarity_metric = 0.0
        try:
            if x['gender'] != y['gender']:
                similarity_metric += weights[0] * 1
        except:
            pass
        try:
            if x['locale'] != y['locale']:
                similarity_metric += weights[1] * 1
        except:
            pass
        try:
            if x['occupation'] != y['occupation']:
                similarity_metric += weights[2] * 1
        except:
            pass
        try:
            similarity_metric += weights[3] * (1 - mean_relevant_locations_distance(x['relevantLocations'], y['relevantLocations']))
        except:
            pass
        try:
            similarity_metric += weights[4] * (1 - common_planned_activities(x['plannedActivities'], y['plannedActivities']))
        except:
            pass
        try:
            similarity_metric += weights[5] * (1 - competences_distance(x['competences'], y['competences']))
        except:
            pass
        try:
            similarity_metric += weights[6] * (1 - meanings_distance(x['meanings'], y['meanings']))
        except:
            pass
        return similarity_metric
    except:
        return similarity_metric
