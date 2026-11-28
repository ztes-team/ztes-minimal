"""Arithmetic reference for the factorization pattern experiment. Python 3.8+."""

from itertools import combinations
from math import gcd, isqrt


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def build_mask(modulus, residue):
    squares = {b * b % modulus for b in range(modulus)}
    return {a for a in range(modulus) if (a * a - residue) % modulus in squares}


def check_mask(modulus, residue, mask):
    witnesses = {(a, b) for a in range(modulus) for b in range(modulus)
                 if (a * a - b * b) % modulus == residue}
    return mask == {a for a, _ in witnesses}


def search(n, modulus=1, mask=None):
    first = isqrt(n - 1) + 1
    required_parity = 1 if n % 4 == 1 else 0
    if first % 2 != required_parity:
        first += 1
    probes = []
    for a in range(first, (n + 1) // 2 + 1, 2):
        if mask is not None and a % modulus not in mask:
            continue
        probes.append(a)
        delta = a * a - n
        b = isqrt(delta)
        if b * b == delta and a - b > 1:
            return (a - b, a + b), probes
    raise ValueError(f"No nontrivial split for {n}")


def discover(source, failed_centers):
    for m in (4, 8, 16):
        residue = source % m
        mask = build_mask(m, residue)
        excluded = sum(a % m not in mask for a in failed_centers)
        if excluded >= 2:
            assert check_mask(m, residue, mask)
            return m, residue, mask
    raise ValueError("Source evidence does not trigger a pattern")


def compare(targets, pattern, show_probes=False):
    m, residue, published = pattern
    kpi = dict(targets=0, compatible=0, fallback=0, improved=0, agreement=0,
               parity_probes=0, fresh_probes=0, reuse_probes=0,
               compatible_parity_probes=0, compatible_reuse_probes=0,
               fresh_target_builds=0, reused_mask_reads=0)
    for n in targets:
        factors, baseline = search(n)
        kpi["targets"] += 1
        if n % m == residue:
            kpi["compatible"] += 1
            fresh_mask = build_mask(m, residue)
            kpi["fresh_target_builds"] += 1
            fresh_factors, fresh = search(n, m, fresh_mask)
            kpi["reused_mask_reads"] += 1
            reused_factors, reused = search(n, m, published)
            kpi["compatible_parity_probes"] += len(baseline)
            kpi["compatible_reuse_probes"] += len(reused)
        else:
            kpi["fallback"] += 1
            fresh_factors, fresh = search(n)
            reused_factors, reused = search(n)
        assert factors == fresh_factors == reused_factors and fresh == reused
        assert factors[0] * factors[1] == n and all(is_prime(p) for p in factors)
        kpi["agreement"] += 1
        kpi["improved"] += len(reused) < len(baseline)
        kpi["parity_probes"] += len(baseline)
        kpi["fresh_probes"] += len(fresh)
        kpi["reuse_probes"] += len(reused)
        if show_probes:
            print(n, factors, "parity", baseline, "fresh", fresh, "reuse", reused)
    return kpi


def main():
    source = 1121
    source_factors, probes = search(source)
    pattern = discover(source, probes[:-1])
    m, residue, mask = pattern
    print("source", source, source_factors, "probes", probes)
    print("selected modulus", m, "residue", residue, "mask", sorted(mask))
    corrupted = {a for a in mask if a % 8 != 1}
    assert not check_mask(m, residue, corrupted)
    print("incomplete mask rejected by exhaustive checker")
    print("illustrative targets", compare([2929, 1643], pattern, show_probes=True))
    primes = [p for p in range(17, 102) if is_prime(p)]
    population = [p*q for p, q in combinations(primes, 2) if gcd(p*q, source) == 1]
    print("whole population", compare(population, pattern))


if __name__ == "__main__":
    main()
