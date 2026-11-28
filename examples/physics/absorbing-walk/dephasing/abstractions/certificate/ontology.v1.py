def omega(A, TRAP, START, Q, U, certs):
    # [ω] Sω of certificate: the ontology searches the graph for twins (D2: the criterion checks).
    #     It reads the regime only (A, START, Q), not the slices: a claim about every continuation.
    if certs > 0 or Q[0] != 0 or U is None:
        return None
    return certify(A, TRAP, initial(len(A), TRAP, START))
