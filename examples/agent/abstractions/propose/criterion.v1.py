def tau(TASKS, DAY, proposals, decisions, w):
    if not all(t in decisions for t in proposals):
        return False
    todo = [x["id"] for x in TASKS if x["day"] == DAY and x["id"] not in proposals]
    return len(todo) > 0 and w["t"] == todo[0]
