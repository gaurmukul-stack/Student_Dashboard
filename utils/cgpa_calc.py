def calculate_cgpa(gpas, credits):
    total_credits = sum(credits)
    weighted_sum = sum(g * c for g, c in zip(gpas, credits))
    return weighted_sum / total_credits
