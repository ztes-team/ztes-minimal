def tau(fundings, prior, w):
    # [τ] Sτ of policy: one policy per funded case, a balance for every tier, routes it may cover, and
    #     precedents among the cases funded before it (the cut that its snapshot will declare).
    f = find_case(fundings, w["case"])
    return (f is not None and find_case(prior, w["case"]) is None and w["ref"] == "policy/" + w["case"]
            and len(w["available"]) == len(f["limits"]) and all(x >= 0 for x in w["available"])
            and all(r in ["transport", "cold_chain"] for r in w["covers"])
            and all(c in earlier(fundings, w["case"]) for c in w["precedents"]))
