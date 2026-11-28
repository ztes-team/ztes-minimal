def omega(FEES, fundings, prior):
    # [ω] Sω of fee: the next debit of the fixture table, once the funding of its case is recorded.
    if len(prior) >= len(FEES) or find_case(fundings, FEES[len(prior)]["case"]) is None:
        return None
    return FEES[len(prior)]
