def omega(COEF, EPS, SHORT, PATH, LO, HI, ANC, tmpl, mine, kids, anc):
    coef = [Fraction(c) for c in COEF]
    lo, hi = Fraction(LO), Fraction(HI)
    if SHORT:
        for e in anc:
            if e["path"] != PATH and e["kind"] != "split":
                return None                                  # an ancestor is decided: this work is abandoned
    if len(mine) == 0:
        b = lower(coef, lo, hi)
        if b > 0:
            return {"path": PATH, "kind": "certified", "v": True, "x": lo, "bound": b, "specifications": []}
        mid = (lo + hi) / 2
        for x in [lo, mid, hi]:
            if value(coef, x) <= 0:
                return {"path": PATH, "kind": "witness", "v": False, "x": x, "bound": b, "specifications": []}
        if hi - lo <= Fraction(EPS) or len(tmpl["specs"]) == 0:
            return None                                      # undecided at this resolution: Not Yet
        return {"path": PATH, "kind": "split", "v": False, "x": mid, "bound": b,
                "specifications": children(tmpl["specs"], PATH, lo, mid, hi, ANC)}
    if len(mine) == 1 and mine[0]["kind"] == "split":
        done = {}
        for e in kids:
            if e["kind"] != "split":
                done[e["path"]] = e
        if len(done) < 2 and not SHORT:
            return None                                      # without short-circuit: wait for both children
        for p in sorted(done):
            if done[p]["v"] == False:
                return {"path": PATH, "kind": "return", "v": False, "x": done[p]["x"],
                        "bound": mine[0]["bound"], "specifications": []}
        if len(done) == 2:
            return {"path": PATH, "kind": "return", "v": True, "x": mine[0]["x"],
                    "bound": mine[0]["bound"], "specifications": []}
    return None
