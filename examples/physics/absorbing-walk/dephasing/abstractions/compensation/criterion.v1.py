def tau(T_DECIDE, last, certificates, decisions, w):
    # [τ] Sτ of compensation: the authority that judges the governing event g (R1, Corollary 9). The
    #     change is admissible only when the record holds a certificate that the earlier regime cannot
    #     reach the goal, and only from the recorded slice at which the walk waits.
    if decisions > 0 or len(certificates) == 0 or last["t"] != T_DECIDE or w["from"] != last["t"]:
        return False
    q = w["q"]
    if len(q) != 2 or not (0 < q[0] <= q[1]):
        return False
    roles = sorted([s.get("abstraction", ""), s.get("role", "")] for s in w["specifications"])
    if roles != [["certificate", "criterion"], ["certificate", "ontology"], ["step", "criterion"], ["step", "ontology"]]:
        return False
    return all(s.get("constants", {}).get("Q") == q for s in w["specifications"])
