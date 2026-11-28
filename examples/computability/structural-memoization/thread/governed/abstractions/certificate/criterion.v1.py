def tau(K, RULES, fundings, snapshots, plans, prior, w):
    # [τ] Sτ of certificate: the bound is the sum of the first K limits of the recorded funding, and the
    #     loss exceeds it. The settle criterion credits at most that bound and the funding of a case is
    #     recorded once, so a full credit is unreachable at every prefix of every continuation of the rules.
    return certificate_valid(w, fundings, snapshots, plans, prior, K, RULES)
