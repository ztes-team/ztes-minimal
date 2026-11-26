def tau(M0, N0, vals, results, w):
    return (w["m"], w["n"]) == (M0, N0) and (M0, N0) not in results and vals.get((M0, N0)) == w["v"]
