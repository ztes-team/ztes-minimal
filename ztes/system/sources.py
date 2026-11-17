"""Occurrences for boundary abstractions: what the environment supplies to an invocation.   Paper: §5.2, S1.4

A boundary abstraction does not compute its candidate from C: the candidate is an occurrence
bound to the invocation, and it becomes a fact of the record only by being admitted. This module
supplies such occurrences during phase 3. system.json declares them:

    "sources": {"draw": {"random": {"seed": 1, "size": 11, "below": 1000000}}}

    random    a list of `size` integers in [0, below), from a generator defined here in full, so
              that the same seed gives the same occurrences on every platform. The seed belongs
              to the environment, not to any specification: what was drawn is in C, and replay
              (R2) reads the recorded draws and never consults the source.

A source is part of the run, not of the calculus: Z₀ sees only the occurrence it is given.
"""

MASK = (1 << 64) - 1


class RandomSource:
    """SplitMix64: a small, fully specified generator (Steele, Lea, Flood 2014)."""

    def __init__(self, seed, size, below):
        """A generator from `seed`; each occurrence is `size` integers below `below`."""
        self.state, self.size, self.below = seed & MASK, size, below

    def _next64(self):
        """The next 64-bit output: the state advances by the golden-ratio constant and is mixed."""
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def next(self):
        """One occurrence: `size` integers in [0, below)."""
        return [self._next64() % self.below for _ in range(self.size)]


KINDS = {"random": RandomSource}


def problems(declared, abstractions):
    """What is wrong with the "sources" of a system.json (empty: nothing)."""
    out = []
    for a, d in declared.items():
        if a not in abstractions:
            out.append(f"sources: {a} is not an abstraction of the system")
        elif not (isinstance(d, dict) and len(d) == 1 and next(iter(d)) in KINDS):
            out.append(f"sources: {a} must be one of {sorted(KINDS)} with its parameters")
        else:
            p = d["random"]
            if not (isinstance(p, dict) and all(isinstance(p.get(f), int) and not isinstance(p.get(f), bool)
                                                for f in ("seed", "size", "below")) and p["size"] > 0 and p["below"] > 0):
                out.append(f'sources: {a}: random needs integers "seed", "size" > 0 and "below" > 0')
    return out


def make(declared):
    """A fresh source for every declared abstraction: each run starts from its seeds."""
    return {a: KINDS[kind](**params) for a, d in declared.items() for kind, params in d.items()}
