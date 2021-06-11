import numpy as np
import json

###############
### Parsing ###
###############

def parse_entity(entity):
    meanings = entity['meanings']
    if meanings is None:
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


def parser(entities):
    #with open(path_to_json, 'r') as file:
     #   entities = json.load(file)
    dict_of_entities = {}
    for entity in entities:
        dict_of_entities[entity['id']] = parse_entity(entity)
    return dict_of_entities


def file_parser(path_to_json):
    with open(path_to_json, 'r') as file:
        entities = json.load(file)
    dict_of_entities = {}
    for entity in entities:
        dict_of_entities[entity['id']] = parse_entity(entity)
    return dict_of_entities

#################################
## Diversity related functions ##
#################################

def entropy(distribution):
    return -sum([p*np.log(p) for p in distribution if p > 0])/np.log(len(distribution))

def multi_dimensional_diversity(list_of_entities, discretization_step=0.05, min_val=0, max_val=1, weights = None): #Assume that all entities are described by the same number of continuous attributes
    n_attributes = len(list_of_entities[0])
    if weights == None:
        weights = [1/n_attributes]*n_attributes
    attributes = [[]]*n_attributes
    for entity in list_of_entities:
        #Take each entity, note all its attributes and consturct n_attr separate lists.
        for i in range(n_attributes):
            attributes[i].append(entity[i])
    distributions = []
    for attribute in attributes:
        distributions.append(continuous_distribution(attribute, discretization_step, min_val, max_val))
    return sum([weights[i]*entropy(distributions[i]) for i in range(n_attributes)])

def continuous_distribution(list_of_values, discretization_step=0.05, min_val=0.0, max_val=1.0):
    n_categories = int(np.ceil((max_val-min_val)/discretization_step))
    if len(list_of_values) == 0:
        return [0.0]*n_categories
    probability_step = 1/len(list_of_values)
    distribution = [0.0]*n_categories
    for x in list_of_values:
        distribution[int(n_categories*(x-min_val)/(max_val-min_val))] += probability_step
    return distribution

def discrete_distribution(list_of_entities):
    category_labels = set(list_of_entities)
    n = len(category_labels)
    distribution = {}
    for label in category_labels:
        distribution[label] = 0.0
    probability_step = 1/len(list_of_entities)
    for x in list_of_entities:
        distribution[x] += probability_step
    return distribution

def diversity_contribution(list_of_entities, entity, disc_step=0.05, min_val=0.0, max_val=1.0):
    if not list_of_entities or not entity in list_of_entities:
        return None
    elif len(list_of_entities) == 1:
        return 0
    removed_list = [x for x in list_of_entities if x != entity]
    dummy_list_1 =  [] #TODO Update according to new diversity calculation methodology!
    dummy_list_2 = []
    for x in list_of_entities:
        dummy_list_1 += x
    for x in removed_list:
        dummy_list_2 += x
    distribution_1 = continuous_distribution(dummy_list_1, disc_step, min_val, max_val)
    distribution_2 = continuous_distribution(dummy_list_2, disc_step, min_val, max_val)
    return entropy(distribution_1) - entropy(distribution_2)

def diversity_scores(dict_of_entities):
    diversity_contributions = {}
    list_of_entities = list(dict_of_entities.values())
    total_contribution = 0
    for entity in list(dict_of_entities.keys()):
        contribution = diversity_contribution(list_of_entities, dict_of_entities[entity])
        diversity_contributions[entity] = contribution
        total_contribution += abs(contribution)
    if total_contribution == 0:
        return None
    for entity in list(diversity_contributions.keys()):
        diversity_contributions[entity] /= total_contribution
    return diversity_contributions

#########################################
### Fitness ranking related functions ###
#########################################

def normalized_euclidean_distance(x, y, weights = None):
    n = len(x)
    if n != len(y):
        return None
    if weights == None:
        return (sum([(x[i] - y[i])**2 for i in range(n)])/n)**0.5
    if len(weights) != n:
        return None
    return (sum([weights[i]*(x[i] - y[i])**2 for i in range(n)])/n)**0.5

def naive_inversor(x):
    return 1 - x

def ranking_scores(dict_of_entities, model, distance_inversor):
    scores = {}
    for entity in list(dict_of_entities.keys()):
        scores[entity] = distance_inversor(normalized_euclidean_distance(dict_of_entities[entity], model))
    return scores

#####################
### Generic stuff ###
#####################

def total_ranking_score(dict_of_entities, model, diversity_coefficient):
    total_scores = {}
    fitness_scores = ranking_scores(dict_of_entities, model, naive_inversor)
    div_scores = diversity_scores(dict_of_entities)
    for entity in list(dict_of_entities.keys()):
        total_scores[entity] = diversity_coefficient*div_scores[entity] + (1-diversity_coefficient)*fitness_scores[entity]
    return total_scores

def rank_entities(dict_of_entities, model, diversity_coefficient):
    scores = total_ranking_score(dict_of_entities, model, diversity_coefficient)
    ranked_list = list({key: value for key, value in sorted(scores.items(), key=lambda item: item[1])}.keys())
    return ranked_list[::-1]

if __name__ == '__main__':
    path_to_json = 'test_vols.json'
    model = [0.5]*5
    diversity_coefficient = 0.4
    dict_of_entities = parser(path_to_json)
    ranking = rank_entities(dict_of_entities, model, diversity_coefficient)
    print(ranking)