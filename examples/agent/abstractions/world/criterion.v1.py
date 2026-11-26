def tau(SCRIPT, k, facts, decisions, w):
    f = next_fact(k, SCRIPT, facts, decisions)
    return f is not None and w == f
