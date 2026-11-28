def tau(fundings, settlements, mandates, prior, w):
    # [τ] Sτ of fee: a positive debit of a party of the case, while the case is unsettled and no mandate
    #     has changed its rules; so the fees of a case are those debited under the earlier rules.
    f = find_case(fundings, w["case"])
    return (f is not None and w["actor"] in parties(f) and w["amount"] > 0 and w["ref"] != ""
            and all(x["ref"] != w["ref"] for x in prior) and find_case(settlements, w["case"]) is None
            and find_case(mandates, w["case"]) is None)
