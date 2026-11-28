def omega(EVIDENCE, fundings, prior):
    # [ω] Sω of evidence: the next observation of the fixture table, once the funding of its case is recorded.
    if len(prior) >= len(EVIDENCE) or find_case(fundings, EVIDENCE[len(prior)]["case"]) is None:
        return None
    return EVIDENCE[len(prior)]
