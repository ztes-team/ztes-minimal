def omega(DECISIONS, certificates, prior):
    # [ω] Sω of board: the next decision of the fixture table, once its certificate is recorded. The
    #     board is an authority outside the parties; its decisions are observations of the record.
    if len(prior) >= len(DECISIONS) or find_case(certificates, DECISIONS[len(prior)]["case"]) is None:
        return None
    return DECISIONS[len(prior)]
