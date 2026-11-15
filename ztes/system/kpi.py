"""Execution indicators (KPI) as abstractions above Z₀, computed on demand.      Paper: §6.3, §8.8, §5.2

KPI are not part of the calculus. They belong to the design of an execution: ordinary abstractions,
admitted by Z₀ under Axiom 0, that are invoked only when an indicator is needed (a plan step
{"kpi": true}; in the examples, once at the end). Since admitted events are immutable,
nothing has to be computed before it is asked for.

Two abstractions take part:

  profile   a boundary abstraction (§5.2). Its candidate is the count of outcomes the agenda has
            observed for each abstraction: I invocations, A admitted, U ⊥ (Not Yet), F τ false
            (n_I, n_A, n_U, n_F in §8.8), and H, the part of U decided by the horizon alone: a
            required event was not in Cⁿ and nothing was computed. U − H is then the number of
            invocations whose body ran on a complete horizon and gave no candidate, and F the
            number whose candidate τ refused; these two are where
            computation is spent without an event.
            U and F leave no event in C, so they enter C only as this observation; the criterion
            checks what C can confirm (A equals the events of that abstraction, I = A + U + F,
            0 ≤ H ≤ U, counts never decrease) and the payload is retained as evidence (S1.4). Its
            specifications are generated for each system.
  kpi       optional, specific to the problem (system.json: "kpi": "<name>", specifications in
            abstractions/<name>/). An ordinary abstraction whose bindings read the latest profile
            and any domain lineage, so it can compute any indicator of that execution, e.g. the
            share of reused subproblems. Abstractions that read its lineage (a heuristic agent)
            see the indicator and are evaluated again after it is admitted.

Counting outcomes is the agenda's own bookkeeping (agenda.py): one counter per invocation.
"""

PROFILE = "profile"
PROFILE_TYPE = {"list": {"record": {"abstraction": "text", "I": "integer", "A": "integer",
                                    "U": "integer", "H": "integer", "F": "integer"}}}
# declarations available to every KPI specification
KPI_TYPES = {"Profile": PROFILE_TYPE}
KPI_BINDINGS = {
    "profile":  {"from": PROFILE, "select": "last", "type": "Profile", "default": [],
                 "note": "the latest observed counts of outcomes"},
    "profiles": {"from": PROFILE, "select": "count", "note": "how many profiles are recorded"},
}


def profile_specs(abstractions):
    """The recorded specifications of the profile abstraction for a system with these abstractions."""
    counts = {f"a{i}": {"from": a, "select": "count"} for i, a in enumerate(abstractions)}
    criterion = {
        "abstraction": PROFILE, "role": "criterion", "version": 1, "returns": "boolean", "total": True,
        "constants": {"ABSTRACTIONS": list(abstractions)},
        "inputs": {"context": {**counts, "prev": {"from": PROFILE, "select": "last", "type": PROFILE_TYPE,
                                                  "default": []}},
                   "candidate": {"name": "w", "type": PROFILE_TYPE}},
        "body": {
            "counts": "[" + ", ".join(counts) + "]",
            "rows": "len(w) == len(ABSTRACTIONS) and all(w[i]['abstraction'] == ABSTRACTIONS[i] "
                    "and w[i]['A'] == counts[i] and w[i]['I'] == w[i]['A'] + w[i]['U'] + w[i]['F'] "
                    "and 0 <= w[i]['H'] <= w[i]['U'] and w[i]['F'] >= 0 for i in range(len(w)))",
            "grows": "len(prev) != len(w) or all(w[i]['I'] >= prev[i]['I'] and w[i]['U'] >= prev[i]['U'] "
                     "and w[i]['H'] >= prev[i]['H'] and w[i]['F'] >= prev[i]['F'] for i in range(len(w)))",
            "result": "rows and grows",
        },
    }
    ontology = {"abstraction": PROFILE, "role": "ontology", "version": 1, "partial": True, "boundary": True,
                "returns": PROFILE_TYPE, "inputs": {"context": {}}}
    return {f"{PROFILE}/criterion.v1": criterion, f"{PROFILE}/ontology.v1": ontology}


def observation(system):
    """The occurrence for profile: the outcomes counted by the agenda so far, in system order."""
    return [{"abstraction": a, **{k: system.outcomes[a][k] for k in ("I", "A", "U", "H", "F")}}
            for a in system.abstractions]


def table(system, C):
    """The latest profile and kpi payloads in C, as data: ({abstraction: row}, kpi payload or None)."""
    last = {}
    for e in C:
        c = e["coord"]
        if c["kind"] == "exec" and c["abstraction"] in (PROFILE, system.kpi):
            last[c["abstraction"]] = e["payload"]
    rows = {r["abstraction"]: r for r in last.get(PROFILE, [])}
    return rows, last.get(system.kpi) if system.kpi else None
