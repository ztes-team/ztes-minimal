def tau(diagnoses, policies, catalogue, prior, w):
    # [τ] Sτ of snapshot: one per diagnosed case; it lists exactly the recorded publications of the
    #     precedents that the policy of the case accepts.
    d = find_case(diagnoses, w["case"])
    policy = find_case(policies, w["case"])
    return (d is not None and policy is not None and find_case(prior, w["case"]) is None
            and w == snapshot_for(d, policy, catalogue))
