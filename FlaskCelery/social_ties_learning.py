def compute_tie_strength(data, type_of_interaction, old_tie_strength):
    sign = 1
    if (type_of_interaction == "negative"):
        sign = -1
    total_interactions = 40#data["total"]
    first = 1457166440#data["firstTs"]
    last = 1571664406#data["lastTs"]
    if (first == last):
        return max(0.5 (old_tie_strength + sign * 0.5), 0)
    return max(0.5 * (old_tie_strength + sign * 2 ** (-total_interactions / (last - first))), 0)