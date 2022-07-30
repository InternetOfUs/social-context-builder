import math
import json

from . import diversity_metrics

# def dist(mu, D_mu):
#     return min([abs(mu - x) for x in D_mu])

class UserNotFoundError(Exception):
    pass

def sort_by(mu, D_mu, X, mu_rank, attributes): # D_mu is a list of length len(X) containing lists of values.
    distances = {}
    # print('mu_rank:', mu_rank)
    for i in range(len(X)):
        if X[i]['id'] in mu_rank:
            # print('id:', X[i]['id'])
            continue
        user_distribution = get_user_multidimensional_distribution(X, mu_rank + [X[i]['id']], attributes)
        distances[X[i]['id']] = abs(mu(user_distribution) - D_mu[len(mu_rank)])
    # distances = {X[i]: abs(mu(get_distribution(mu_rank + [X[i]], classes)) - D_mu[len(mu_rank)]) for i in range(len(X)) if X[i] not in mu_rank}
    return list({x: val for x, val in sorted(distances.items(), key=lambda item: item[1], reverse=True)}.keys())

def get_user_by_id(sample, id):
    for user in sample:
        if user["id"] == id:
            return user
    raise UserNotFoundError

def get_user_multidimensional_distribution(sample, users, attributes):
    distribution = {}
    for attribute in attributes:
        distribution[attribute] = get_user_distribution(sample, users, attribute)
    return distribution

def get_user_distribution(sample, users, attribute = 'meanings'):
    distribution = {}
    for user_id in users:
        try:
            user = get_user_by_id(sample, user_id)
        except UserNotFoundError:
            continue
        try:
            user_attribute = user[attribute]
        except KeyError:
            continue
        if attribute == 'meanings':
            max_meaning = get_max_meaning(user_attribute)
            if max_meaning == None:
                continue
            if max_meaning['name'] in distribution.keys():
                distribution[max_meaning['name']] += 1
            else:
                distribution[max_meaning['name']] = 1
        elif attribute in ['gender', 'nationality', 'occupation']:
            if user_attribute in distribution.keys():
                distribution[user_attribute] += 1
            else:
                distribution[user_attribute] = 1
        else:
            raise KeyError
    return distribution

def get_max_meaning(meanings):
    try:
        if not meanings:
            return None
        max_meaning = meanings[0]
        for meaning in meanings[1:]:
            if meaning['level'] > max_meaning['level']:
                max_meaning = meaning
        return max_meaning
    except:
        return None

"""
Non recursive Shuffle2:
front: a stack, initially contains a ranking of X according to SortBy.
muRank = empty list
While (front != empty && len(X) > len(muRank)):
    next_el = front.pop()
    muRank.append(next_el)
    if ell_1(rank, muRank) > d_max:
        muRank.pop()
    else:
        front += sortBy(mu, D_mu, X \ muRank)
"""

def shuffle2(X, d_max, crisp_ranking, cut_off, diversity_metric = diversity_metrics.multidimensional_diversity, attributes = ['meanings']): # NON-recursive version of Shuffle2 algorithm
    d_div = [1.0] * cut_off
    mu_rank = []
    front = [None]
    front += sort_by(diversity_metric, d_div, X, mu_rank, attributes)
    # print(front)
    while (len(front) > 0 and len(X) > len(mu_rank)):
        next_el = front.pop()
        if next_el == None:
            try:
                mu_rank.pop()
            except IndexError:
                return crisp_ranking[:cut_off]
            continue
        if next_el in mu_rank:
            continue
        mu_rank.append(next_el)
        # if normalized_ell_1(crisp_ranking, mu_rank) > d_max:
        #     mu_rank.pop()
        if hamming_distance(crisp_ranking, mu_rank, cut_off) > d_max:
            mu_rank.pop()
        elif len(mu_rank) == cut_off:
            # print(hamming_distance(crisp_ranking, mu_rank, cut_off))
            return mu_rank# + [x for x in crisp_ranking if x not in mu_rank]
        elif len(X) == len(mu_rank):
            return mu_rank
        else:
            front.append(None)
            front += sort_by(diversity_metric, d_div, X, mu_rank, attributes)
    return crisp_ranking[:cut_off]

def update_class_distribution(X, mu_rank, classes):
    distribution = [0] * len(classes)
    for x in X:
        if x not in mu_rank:
            distribution[classes[str(x[0]) + ',' + str(x[1])]] += 1
    return distribution

def normalized_ell_1(x, y):
    n = len(x)
    return 1 / math.ceil(0.5 * (n ** 2 - 1)) * ell_1(x, y)

def hamming_distance(x, y, cut_off):
    dist = 0
    n = min(cut_off, len(x), len(y))
    for x_i in x[:n]:
        if x_i not in y[:n]:
            dist += 1
    return dist

def ell_1(x, y):
    n = min(len(x), len(y))
    if n < 1:
        return 0
    perm = find_permutation(x, y)
    return sum([abs(i - perm[i]) for i in range(n)])

def find_permutation(rank_1, rank_2): # IMPORTANT! Assumes that rank_1 has the most points in it!
    n = min(len(rank_1), len(rank_2))
    return [rank_1.index(rank_2[i]) for i in range(n)]

def main():
    with open('100_vols_dataset.json') as file:
        all_users = json.load(file)
    cut_off = 5
    n = 10
    sample_users = all_users[:n]
    d_max = 2
    # d_div = [1.0] * n
    # div_metric = diversity_metrics.multidimensional_diversity
    crisp_ranking = [x["id"] for x in sample_users]
    shuffled_ranking = shuffle2(sample_users, d_max, crisp_ranking, cut_off)
    print(crisp_ranking, shuffled_ranking)

if __name__ =='__main__':
    main()

# FIXME Return only the first 5 (or so) elements with the restriction at most 2 (40%) of them to be different!
# Input: The cutoff-threshold and the number of different instances that differ.
# Create a non-technical report describing the above, with a couple of examples.