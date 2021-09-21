#Learning component of diversity aware ranking mechanism

from itertools import product
import json

###############
### Parsing ###
###############

def parse_entity(entity):
    meanings = entity['meanings']
    if meanings == None:
        return [0.5]*5
    ocean = [0.0]*5
    for meaning in meanings:
        if meaning['name'] == 'openess':
            ocean[0] = meaning['level']
        elif meaning['name'] == 'consientiousness':
            ocean[1] = meaning['level']
        elif meaning['name'] == 'extraversion':
            ocean[2] = meaning['level']
        elif meaning['name'] == 'agreeableness':
            ocean[3] = meaning['level']
        elif meaning['name'] == 'neuroticism':
            ocean[4] = meaning['level']
    return ocean

def parser(path_to_json):
    with open(path_to_json, 'r') as file:
        entities = json.load(file)
    list_of_entities = []
    for entity in entities:
        list_of_entities.append(parse_entity(entity))
    return list_of_entities


def jsonparser(entities):
    list_of_entities = []
    for entity in entities:
        list_of_entities.append(parse_entity(entity))
    return list_of_entities

################
### Learning ###
################

def contained_in(half_spaces, temp_vol):
    for (slope, mid) in half_spaces:
        if inner_prod([temp_vol[i] - mid[i] for i in range(len(mid))], slope) > 0: #TODO check again!
            return False
    return True

def inner_prod(x, y):
    prod = 0
    for i in range(len(x)):
        prod += x[i]*y[i]
    return prod

def grid_based_centroid(half_spaces, grid, d):
    # print(half_spaces)
    grid = [x for x in grid if contained_in(half_spaces, x)]
    k = len(grid)
    if k == 0:
        return None
    centroid = [0.0]*d
    for x in grid:
        centroid = [x[i] + centroid[i] for i in range(d)]
    centroid = [x/k for x in centroid]
    return centroid

def grid_initialization(d, epsilon=None):
    if epsilon == None:
        epsilon = 10**(-0.1*d)
    k = int(1./epsilon)
    main_axis = [0.0]*k
    for i in range(1,k):
        main_axis[i] = main_axis[i-1] + epsilon
    grid = [list(x) for x in product(main_axis, repeat=d)]
    return grid

def get_half_spaces(suggested_entities, preferred, N=0):
    half_spaces = []
    if N == 0:
        N = len(suggested_entities)
    for i in range(1,min(N,len(suggested_entities))):
        temp_vol = suggested_entities[i]
        mid = [(preferred[i] + temp_vol[i])/2 for i in range(len(preferred))]
        slope = [temp_vol[i] - preferred[i] for i in range(len(preferred))]
        half_spaces.append((slope, mid))
    return half_spaces

def ranking_model(user_preference, suggested_entities):
    d = len(user_preference)
    half_spaces = get_half_spaces(suggested_entities, user_preference)
    grid = grid_initialization(d)
    model = grid_based_centroid(half_spaces, grid, d)
    return model

if __name__ == '__main__':
    path_to_suggestions = 'suggestions.json'
    suggested_entities = parser(path_to_suggestions)
    print( suggested_entities)
    user_preference = suggested_entities[0] #dummy, as for now
    print (user_preference)
    model = ranking_model(user_preference, suggested_entities)
    print(model)