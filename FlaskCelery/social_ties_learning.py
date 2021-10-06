def compute_tie_strength(data, type_of_interaction, old_tie_strength, first_last_total_interaction):
    sign = 1
    if type_of_interaction == "negative":
        sign = -1
    total_interactions = int(first_last_total_interaction.get('total'))
    first = int(first_last_total_interaction.get('first'))
    last = int(first_last_total_interaction.get('last'))
    if first == last:
        return max(0.5 (old_tie_strength + sign * 0.5), 0)
    return max(0.5 * (old_tie_strength + sign * 2 ** (-total_interactions / (last - first))), 0)
