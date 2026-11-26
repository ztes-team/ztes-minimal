def tau(COEF, EPS, SHORT, PATH, LO, HI, ANC, tmpl, mine, kids, w):
    coef = [Fraction(c) for c in COEF]
    lo, hi = Fraction(LO), Fraction(HI)
    if w["path"] != PATH:
        return False
    k = w["kind"]
    if k == "certified":                                     # termination: p > 0 is proved on [LO, HI]
        return (len(mine) == 0 and w["v"] == True and len(w["specifications"]) == 0
                and w["bound"] == lower(coef, lo, hi) and w["bound"] > 0)
    if k == "witness":                                       # termination: a point where p <= 0
        return (len(mine) == 0 and w["v"] == False and len(w["specifications"]) == 0
                and lo <= w["x"] <= hi and value(coef, w["x"]) <= 0)
    if k == "split":                                         # the children are this criterion, specialized
        mid = (lo + hi) / 2
        return (len(mine) == 0 and lower(coef, lo, hi) <= 0 and hi - lo > Fraction(EPS) and w["x"] == mid
                and are_children(w["specifications"], tmpl["specs"], PATH, lo, mid, hi, ANC))
    if k == "return":                                        # back up: positive atoms of the children
        if len(mine) != 1 or mine[0]["kind"] != "split" or len(w["specifications"]) != 0:
            return False
        done = {}
        for e in kids:
            if e["kind"] != "split":
                done[e["path"]] = e
        false = [done[p] for p in sorted(done) if done[p]["v"] == False]
        if not SHORT:
            if len(done) < 2:
                return False
            if w["v"] == False:
                return len(false) > 0 and false[0]["x"] == w["x"]
            return len(false) == 0
        if w["v"] == False:
            return any(e["x"] == w["x"] for e in false)
        return len(done) == 2 and len(false) == 0
    return False
