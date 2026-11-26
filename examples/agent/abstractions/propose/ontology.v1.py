def omega(TASKS, DAY, proposals, decisions):
    if not all(t in decisions for t in proposals):
        return None
    todo = [x["id"] for x in TASKS if x["day"] == DAY and x["id"] not in proposals]
    return {"t": todo[0]} if todo else None
