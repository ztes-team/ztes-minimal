def tau(fundings, certificates, prior, w):
    # [τ] Sτ of board: only the authority named in the funding of the case decides, only on a recorded
    #     certificate, once per case. A decision by a party of the case is refused.
    f = find_case(fundings, w["case"])
    c = find_case(certificates, w["case"])
    return (f is not None and c is not None and find_case(prior, w["case"]) is None
            and w["ref"] == "decision/" + w["case"] and w["issuer"] == f["authority"]
            and w["certificate"] == c["ref"] and w["action"] == "activate-reserve")
