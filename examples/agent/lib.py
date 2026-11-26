# Helpers shared by the specifications of `agent`. A helper reads only its arguments.


def task(tasks, t):
    """The task with number t (tasks are numbered from 1, in order)."""
    return tasks[t - 1]


def facts_of(facts, kind, t):
    """The recorded outside facts of one kind about task t, in record order."""
    return [f for f in facts if f["kind"] == kind and f["t"] == t]


def has(facts, kind, t):
    return len(facts_of(facts, kind, t)) > 0


def consent(tsk, facts):
    """Ethics: every affected party said yes and none said no. Read once the deadline is recorded,
    after which no answer about the task is admissible, so the answers are final."""
    answers = facts_of(facts, "answer", tsk["id"])
    yes = set(a["party"] for a in answers if a["yes"])
    no = set(a["party"] for a in answers if not a["yes"])
    return all(p in yes for p in tsk["parties"]) and len(no) == 0


def settled(t, tasks, facts, decisions):
    """Every task before t is decided, and every executed one is measured: a finite conjunction of
    positive atoms. None while something is missing."""
    for i in range(1, t):
        if i not in decisions:
            return False
        if decisions[i] and not has(facts, "measure", i):
            return False
    return True


def battery_before(t, tasks, facts, decisions, start, capacity):
    """The battery when task t is judged: the start, plus the recorded sun of every task up to t,
    minus the measured battery use of every executed task before t, never above the capacity.
    None while a fact it needs is not recorded."""
    if not settled(t, tasks, facts, decisions):
        return None
    b = start
    for i in range(1, t + 1):
        sun = facts_of(facts, "sun", i)
        if len(sun) == 0:
            return None
        b = min(capacity, b + sun[0]["kwh"])
        if i < t and decisions[i]:
            b = b - facts_of(facts, "measure", i)[0]["kwh"]
    return b


def energy_verdict(t, tasks, facts, decisions, start, capacity, diesel_max):
    b = battery_before(t, tasks, facts, decisions, start, capacity)
    if b is None:
        return None
    need = task(tasks, t)["kwh"]
    if b >= need:
        return {"t": t, "v": True, "battery": b, "diesel": 0}
    if need - b <= diesel_max:
        return {"t": t, "v": True, "battery": b, "diesel": need - b}
    return {"t": t, "v": False, "battery": b, "diesel": 0}


def overruns(t, tasks, facts, decisions):
    """The executed tasks before t whose measured water exceeded the plan: task → excess."""
    out = {}
    for i in range(1, t):
        if decisions.get(i):
            m = facts_of(facts, "measure", i)[0]
            if m["water"] > task(tasks, i)["water"]:
                out[i] = m["water"] - task(tasks, i)["water"]
    return out


def ecology_verdict(t, tasks, facts, decisions, energy, comps, water_budget, co2_budget, co2_per_kwh):
    """Water and CO₂ of the day of task t, with t, within budget; every earlier overrun compensated.
    None while a fact it needs is not recorded. CO₂ is in tenths of a kilogram."""
    if t not in energy or not settled(t, tasks, facts, decisions):
        return None
    over = overruns(t, tasks, facts, decisions)
    if not all(i in comps for i in over):
        return None
    day = task(tasks, t)["day"]
    water, co2 = 0, 0
    for i in range(1, t):
        if decisions[i] and task(tasks, i)["day"] == day:
            m = facts_of(facts, "measure", i)[0]
            water += m["water"]
            co2 += m["diesel"] * co2_per_kwh
    water += task(tasks, t)["water"]
    co2 += energy[t]["diesel"] * co2_per_kwh
    return {"t": t, "v": water <= water_budget and co2 <= co2_budget, "water": water, "co2": co2}


def next_fact(k, script, facts, decisions):
    """The k-th fact of the script as it is recorded, or None while it cannot be: a measurement waits
    for the decision on its task, and is empty if the task was not executed."""
    if k >= len(script):
        return None
    s = script[k]
    f = {"i": k, "kind": s["kind"], "t": s["t"], "party": s.get("party", ""), "yes": s.get("yes", False),
         "kwh": s.get("kwh", 0), "diesel": s.get("diesel", 0), "water": s.get("water", 0), "executed": False}
    if s["kind"] == "answer" and has(facts, "deadline", s["t"]):
        return None                                   # after the deadline no answer is admissible
    if s["kind"] == "measure":
        if s["t"] not in decisions:
            return None
        f["executed"] = decisions[s["t"]]
        if not f["executed"]:
            f["kwh"], f["diesel"], f["water"] = 0, 0, 0
    return f
