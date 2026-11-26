def value(coef, x):
    s = Fraction(0)
    p = Fraction(1)
    for c in coef:
        s += c * p
        p *= x
    return s


def lower(coef, lo, hi):
    s = Fraction(0)
    i = 0
    for c in coef:
        s += c * (lo ** i if c >= 0 else hi ** i)
        i += 1
    return s


def children(tmpl, path, lo, mid, hi, anc):
    out = []
    up = [x for x in anc] + [path]
    for name, a, b in [(path + "0", lo, mid), (path + "1", mid, hi)]:
        for t in tmpl:
            ctx = {}
            for key, bnd in t["inputs"]["context"].items():
                nb = {kk: vv for kk, vv in bnd.items()}
                if key == "mine":
                    nb["from"] = name
                if key == "kids":
                    nb["from"] = [name + "0", name + "1"]
                if key == "anc":
                    nb["from"] = up
                ctx[key] = nb
            inputs = {kk: vv for kk, vv in t["inputs"].items()}
            inputs["context"] = ctx
            cons = {kk: vv for kk, vv in t["constants"].items()}
            cons["PATH"] = name
            cons["LO"] = f"{a}"
            cons["HI"] = f"{b}"
            cons["ANC"] = up
            s = {kk: vv for kk, vv in t.items() if kk != "criterion"}
            s["abstraction"] = name
            s["constants"] = cons
            s["inputs"] = inputs
            out.append(s)
    return out


def as_list(v):
    return [x for x in v]


def same_spec(s, e):
    if sorted(k for k in s if k != "criterion") != sorted(k for k in e if k != "criterion"):
        return False
    for k in ["abstraction", "role", "version", "body", "returns"]:
        if s.get(k) != e.get(k):
            return False
    if s.get("library", "") != e.get("library", ""):
        return False
    if sorted(s["constants"]) != sorted(e["constants"]):
        return False
    for k in e["constants"]:
        a, b = s["constants"][k], e["constants"][k]
        if k in ["ANC", "COEF"]:
            a, b = as_list(a), as_list(b)
        if a != b:
            return False
    if s["inputs"].get("candidate") != e["inputs"].get("candidate"):
        return False
    if sorted(s["inputs"]["context"]) != sorted(e["inputs"]["context"]):
        return False
    for k in e["inputs"]["context"]:
        a, b = s["inputs"]["context"][k], e["inputs"]["context"][k]
        if sorted(a) != sorted(b):
            return False
        for kk in b:
            x, y = a[kk], b[kk]
            if kk == "from" and k in ["kids", "anc"]:
                x, y = as_list(x), as_list(y)
            if x != y:
                return False
    return True


def are_children(specs, tmpl, path, lo, mid, hi, anc):
    expected = children(tmpl, path, lo, mid, hi, anc)
    if len(specs) != len(expected):
        return False
    for i in range(len(expected)):
        if not same_spec(specs[i], expected[i]):
            return False
    return True
