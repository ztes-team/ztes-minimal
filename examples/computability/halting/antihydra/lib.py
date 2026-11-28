# Helper functions shared by the specifications of the antihydra system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# The rules of Antihydra (bbchallenge.org/antihydra): start with a = 8, b = 0; at each step b grows
# by 2 if a is even and falls by 1 if a is odd, and a becomes a + ⌊a/2⌋. The machine halts when
# b = −1. That these rules describe the six-state machine 1RB1RA_0LC1LE_1LD1LC_1LA0LB_1LF1RE_---0RA
# is a lemma of bbchallenge; this system executes the rules.


def start():
    """Step 0."""
    return {"k": 0, "a": 8, "b": 0}


def rule(s):
    """The step after s (s is not halting)."""
    return {"k": s["k"] + 1, "a": s["a"] + s["a"] // 2, "b": s["b"] + 2 if s["a"] % 2 == 0 else s["b"] - 1}


def digits(a):
    """The number of decimal digits of a > 0."""
    d = 0
    for i in range(100000):
        if a == 0:
            break
        a = a // 10
        d += 1
    return d


def measure(steps, profile, profiles):
    """The indicators of the antihydra execution (KPI abstraction)."""
    last = steps[-1]
    even = len([s for s in steps[:-1] if s["a"] % 2 == 0])
    return {"profile": profiles, "steps": last["k"], "b": last["b"], "even": even, "odd": last["k"] - even,
            "lowest_b": min(s["b"] for s in steps), "digits_of_a": digits(last["a"]),
            "halted": any(s["b"] == -1 for s in steps)}
