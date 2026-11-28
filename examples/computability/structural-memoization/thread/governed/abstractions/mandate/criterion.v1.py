def tau(K, fundings, certificates, decisions, prior, w):
    # [τ] Sτ of mandate: the criterion in force that judges the governing event (R1, Corollary 9). The
    #     change is admissible only when the record holds a certificate and the decision of the authority
    #     named in the contract, it names new rules, it carries the same number of tiers k > K to plan,
    #     settle and certificate, and k tiers can pay the certified loss.
    c = find_case(certificates, w["case"])
    d = find_case(decisions, w["case"])
    f = find_case(fundings, w["case"])
    if (len(prior) > 0 or c is None or d is None or f is None or w["ref"] != "mandate/" + w["case"]
            or w["certificate"] != c["ref"] or w["decision"] != d["ref"] or d["issuer"] != f["authority"]
            or d["action"] != "activate-reserve" or w["rules"] == c["rules"]):
        return False
    roles = sorted([s.get("abstraction", ""), s.get("role", "")] for s in w["specifications"])
    if roles != [["certificate", "criterion"], ["certificate", "ontology"], ["plan", "criterion"],
                 ["plan", "ontology"], ["settle", "criterion"], ["settle", "ontology"]]:
        return False
    ks = [s.get("constants", {}).get("K", 0) for s in w["specifications"]]
    return (all(x == ks[0] for x in ks) and ks[0] > K and bound_of(f, ks[0]) >= c["loss"]
            and all(s.get("constants", {}).get("RULES") == w["rules"] for s in w["specifications"]))
