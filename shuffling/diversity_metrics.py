import math

def p_distance(x, y, p=2):
    if x == None or y == None:
        return None
    if (len(x) != len(y)):
        return None
    return sum([(abs(x[i] - y[i])) ** p for i in range(len(x))]) ** (1 / p) / math.sqrt(len(x))

def inner_product(x, y):
    if x == None or y == None:
        return None
    if (len(x) != len(y)):
        return None
    return sum([x[i] * y[i] for i in range(len(x))])

def cosine_simlarity(x, y):
    return inner_product(x, y) / (math.sqrt(inner_product(x, x) * inner_product(y, y)))

def richness(class_distribution):
    size = len(class_distribution)
    # print(class_distribution)
    return len([x for x in class_distribution if x > 0]) / size

def berger_parker_index(class_distribution):
    size = sum(class_distribution)
    return max(class_distribution) / size

def simpson_index(class_distribution):
    size = sum(class_distribution)
    return sum([(x / size) ** 2 for x in class_distribution])

def shannon_index(class_distribution):
    size = sum(class_distribution)
    denominator = 1
    if size > 1:
        denominator = math.log(size)
    return -sum([(x / size) * math.log(x / size) for x in class_distribution if x > 0]) / denominator

def hill_numbers(class_distribution, q=2):
    size = sum(class_distribution)
    if (q < 1):
        return None
    if (q == 1): # Extreme case of Hill numbers
        return math.exp(-sum([(x / size) * math.log(x / size) for x in class_distribution if x > 0]))
    return sum([(x / size) ** q for x in class_distribution]) ** (1 / (1 - q)) / len(class_distribution)

def similarity_diversity(sample, similarity, weights=None):
    n = len(sample)
    d = len(sample[0])
    diversity = 0
    if weights == None:
        for i in range(n):
            for j in range(i):
                if j > 0:
                    weights.append([2 / (n * (n-1))] ** j)
                else:
                    weights.append([])
    for i in range(n):
        for j in range(i):
            diversity += weights[i][j] * similarity(sample[i], sample[j])
    return diversity

def multidimensional_diversity(class_distribution, diversity_metric = simpson_index, weights = None):
    n = len(class_distribution.keys())
    total_diversity = 0
    if weights == None:
        weights = {x: 1 / n for x in class_distribution.keys()}
    for (attribute, distribution) in class_distribution.items():
        total_diversity += weights[attribute] * diversity_metric(list(distribution.values()))
    return total_diversity