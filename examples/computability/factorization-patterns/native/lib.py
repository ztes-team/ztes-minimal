def parity_centers(n):
    first = isqrt(n - 1) + 1
    parity = 1 if n % 4 == 1 else 0
    if first % 2 != parity:
        first += 1
    return range(first, (n + 1) // 2 + 1, 2)


def mask_for(m, residue):
    squares = {b * b % m for b in range(m)}
    return [a for a in range(m) if (a * a - residue) % m in squares]


def propose_plan(targets, plans, patterns, changes, policy):
    if not targets or (plans and plans[-1]["n"] == targets[-1]):
        return None
    n = targets[-1]
    mode = "parity"
    modulus, residue, mask = 0, 0, []
    pattern_ref, activation_ref = "", ""
    if policy != "parity":
        if not changes or not patterns:
            return None
        pattern, change = patterns[0], changes[0]
        pattern_ref, activation_ref = pattern["ref"], change["ref"]
        modulus, residue = pattern["modulus"], pattern["residue"]
        mode = policy if n % modulus == residue else "fallback"
        if mode == "fresh":
            mask = mask_for(modulus, residue)
        elif mode == "reuse":
            mask = pattern["mask"]
    return {"ref": f"plan/{n}", "n": n, "target_ref": f"target/{n}", "mode": mode,
            "pattern_ref": pattern_ref, "activation_ref": activation_ref,
            "modulus": modulus, "residue": residue, "mask": mask}


def valid_plan(w, targets, plans, patterns, changes):
    if not targets or (plans and plans[-1]["n"] == targets[-1]):
        return False
    n = targets[-1]
    if w["n"] != n or w["target_ref"] != f"target/{n}" or w["ref"] != f"plan/{n}":
        return False
    if not changes:
        return (w["mode"] == "parity" and w["pattern_ref"] == w["activation_ref"] == ""
                and w["modulus"] == w["residue"] == 0 and w["mask"] == [])
    if not patterns:
        return False
    publication, change = patterns[0], changes[0]
    if (change["pattern_ref"] != publication["ref"] or w["pattern_ref"] != publication["ref"]
            or w["activation_ref"] != change["ref"] or w["modulus"] != publication["modulus"]
            or w["residue"] != publication["residue"]):
        return False
    if n % w["modulus"] != w["residue"]:
        return w["mode"] == "fallback" and w["mask"] == []
    return w["mode"] == change["materialization"] and w["mask"] == publication["mask"]


def probe_block(plans, blocks):
    if not plans or (blocks and blocks[-1]["n"] == plans[-1]["n"]):
        return None
    plan = plans[-1]
    n = plan["n"]
    centers, differences = [], []
    for a in parity_centers(n):
        if plan["mask"] and a % plan["modulus"] not in plan["mask"]:
            continue
        d = a * a - n
        centers.append(a)
        differences.append(d)
        b = isqrt(d)
        if b * b == d and a - b > 1:
            return {"ref": f"probes/{n}", "n": n, "plan_ref": plan["ref"],
                    "centers": centers, "differences": differences}
    return None


def valid_block(w, plans, blocks):
    if not plans or (blocks and blocks[-1]["n"] == plans[-1]["n"]):
        return False
    plan = plans[-1]
    n = plan["n"]
    centers, ds = w["centers"], w["differences"]
    if (w["n"] != n or w["ref"] != f"probes/{n}" or w["plan_ref"] != plan["ref"]
            or not centers or len(centers) != len(ds)):
        return False
    first = isqrt(n - 1) + 1
    last = centers[-1]
    if last < first or last > (n + 1) // 2:
        return False
    allowed_parity = 1 if n % 4 == 1 else 0
    expected = [a for a in range(first, last + 1) if a % 2 == allowed_parity and
                (not plan["mask"] or a % plan["modulus"] in plan["mask"])]
    if expected != centers:
        return False
    for i in range(len(centers)):
        a = centers[i]
        d = a * a - n
        b = isqrt(d)
        if d != ds[i] or ((b * b == d and a - b > 1) != (i == len(ds) - 1)):
            return False
    return True


def factor_candidate(blocks, factors):
    if not blocks or (factors and factors[-1]["n"] == blocks[-1]["n"]):
        return None
    block = blocks[-1]
    n = block["n"]
    a, b = block["centers"][-1], isqrt(block["differences"][-1])
    pair = [a - b, a + b]
    evidence = [[p % d for d in range(2, isqrt(p) + 1)] for p in pair]
    return {"ref": f"factor/{n}", "n": n, "probes_ref": block["ref"],
            "factors": pair, "prime_remainders": evidence}


def valid_factor(w, blocks, factors):
    if not blocks or (factors and factors[-1]["n"] == blocks[-1]["n"]):
        return False
    block = blocks[-1]
    n = block["n"]
    pair, evidence = w["factors"], w["prime_remainders"]
    if (w["n"] != n or w["ref"] != f"factor/{n}" or w["probes_ref"] != block["ref"]
            or len(pair) != 2 or len(evidence) != 2 or min(pair) < 2 or pair != sorted(pair)
            or prod(pair) != n or sum(pair) != 2 * block["centers"][-1]):
        return False
    for i in range(2):
        p = pair[i]
        remainders = [p % d for d in range(2, isqrt(p) + 1)]
        if 0 in remainders or evidence[i] != remainders:
            return False
    return True


def make_diagnosis(blocks, diagnoses):
    # Only the source, the first factored input, can motivate a pattern; later targets cannot.
    if diagnoses:
        return None
    for block in blocks[:1]:
        failed = block["centers"][:-1]
        if len(failed) >= 2:
            n = block["n"]
            return {"ref": f"diagnosis/{n}", "n": n, "probes_ref": block["ref"],
                    "failed_centers": failed, "threshold": 2}
    return None


def propose_pattern(diagnoses, patterns):
    if patterns or not diagnoses:
        return None
    diagnosis = diagnoses[0]
    n = diagnosis["n"]
    for m in [4, 8, 16]:
        mask = mask_for(m, n % m)
        excluded = sum(a % m not in mask for a in diagnosis["failed_centers"])
        if excluded >= diagnosis["threshold"]:
            return {"ref": f"pattern/{n}", "n": n, "diagnosis_ref": diagnosis["ref"],
                    "modulus": m, "residue": n % m, "mask": mask}
    return None


def valid_pattern(w, diagnoses, patterns):
    if patterns or not diagnoses:
        return False
    diagnosis = diagnoses[0]
    n = diagnosis["n"]
    if w["n"] != n or w["ref"] != f"pattern/{n}" or w["diagnosis_ref"] != diagnosis["ref"]:
        return False
    for m in [4, 8, 16]:
        residue = n % m
        # Audit all residue classes, including ones not reached by the source.
        allowed = [a for a in range(m) if any((a*a - b*b) % m == residue for b in range(m))]
        excluded = sum(a % m not in allowed for a in diagnosis["failed_centers"])
        if excluded >= diagnosis["threshold"]:
            return w["modulus"] == m and w["residue"] == residue and w["mask"] == allowed
    return False


def change_candidate(diagnoses, patterns, changes, policy, successor):
    if not diagnoses or not patterns or changes:
        return None
    p = patterns[0]
    return {"ref": f"activate/{p['n']}", "diagnosis_ref": diagnoses[0]["ref"],
            "pattern_ref": p["ref"], "materialization": policy, "specifications": successor}


def valid_change(w, diagnoses, patterns, changes, policy, successor):
    if changes or not diagnoses or not patterns or len(w["specifications"]) != 1:
        return False
    d, p = diagnoses[0], patterns[0]
    spec = w["specifications"][0]
    # Z0 binds the prospective ontology to the criterion active in the preceding prefix.
    return (p["diagnosis_ref"] == d["ref"] and w["diagnosis_ref"] == d["ref"]
            and w["pattern_ref"] == p["ref"] and w["ref"] == f"activate/{p['n']}"
            and w["materialization"] == policy
            and {k: v for k, v in spec.items() if k != "criterion"} == successor[0])
