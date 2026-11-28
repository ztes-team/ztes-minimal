def omega(snapshots, plans, catalogue, certificates, fees, refunds, closures, profiles, kpis):
    # [ω] Sω of kpi: per target the origin of its plan and the work of the search; per pattern its rules
    #     and the cases that used it; the certificates, the fees against the refunds, and the closures.
    if profiles == 0 or kpis >= profiles:
        return None                                    # ⊥: nothing new to measure
    m = measure(snapshots, plans, catalogue)
    m["certificates"] = [c["case"] for c in certificates]
    m["debited"] = sum(x["amount"] for x in fees)
    m["refunded"] = sum(r["amount"] for r in refunds)
    m["closed"] = [c["case"] for c in closures]
    return m
