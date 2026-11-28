def tau(fundings, prior, w):
    # [τ] Sτ of evidence: an observation of a known kind, issued by someone, for a funded case.
    return (find_case(fundings, w["case"]) is not None and w["ref"] == w["case"] + "/" + w["kind"]
            and w["kind"] in ["inspection", "temperature", "quality"] and w["issuer"] != ""
            and all(e["ref"] != w["ref"] for e in prior))
