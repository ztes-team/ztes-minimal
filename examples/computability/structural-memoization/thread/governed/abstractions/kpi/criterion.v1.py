def tau(snapshots, plans, catalogue, certificates, fees, refunds, closures, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    m = measure(snapshots, plans, catalogue)
    m["certificates"] = [c["case"] for c in certificates]
    m["debited"] = sum(x["amount"] for x in fees)
    m["refunded"] = sum(r["amount"] for r in refunds)
    m["closed"] = [c["case"] for c in closures]
    return profiles > kpis and w == m
