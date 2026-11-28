def omega(POLICIES, fundings, prior):
    # [ω] Sω of policy: the next observation of the fixture table, once the funding of its case is recorded.
    if len(prior) >= len(POLICIES) or find_case(fundings, POLICIES[len(prior)]["case"]) is None:
        return None
    return POLICIES[len(prior)]
