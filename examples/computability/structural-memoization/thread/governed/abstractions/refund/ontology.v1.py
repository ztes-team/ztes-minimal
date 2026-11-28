def omega(mandates, fees, prior):
    # [ω] Sω of refund: the compensation of §6.5 and §9.3. The affected parties follow from the record:
    #     every party with a fee debited for the case under the earlier rules.
    return next_refund(mandates, fees, prior)
