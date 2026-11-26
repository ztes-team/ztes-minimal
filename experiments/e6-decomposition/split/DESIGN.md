# E6. Decomposition by specializing the criterion: design

*Experiment E6 of [`experiments/README.md`](../../README.md). Base paper: R1, D2, Definition 6, Corollary 7.*

**What this system shows.** A problem that divides itself. Every subproblem is a **new abstraction**,
brought in during the run, whose eschatological criterion is the criterion of its parent specialized
to a smaller domain. A node ends by its termination criterion; otherwise it splits, and when its
children are decided it returns their verdict upward.

## 1. Problem

Prove that p(x) = 9000 (x − 1/3)² + 9 = 9000x² − 6000x + 1009 is positive on [0, 1]. Its minimum,
9, is at x = 1/3, where p touches its margin with contact of order k = 2.

## 2. The criterion and its specializations

A node with path π (n, n0, n01, …) owns the interval [LO, HI] that π selects by halving [0, 1]. Its
criterion is the predicate "p > 0 on [LO, HI]", and it admits one of four events:

| Event | When | Meaning |
|---|---|---|
| `certified` | the lower bound of p on [LO, HI] (interval arithmetic in exact rationals) is > 0 | termination: True, with the bound as certificate |
| `witness` | a point x in [LO, HI] with p(x) ≤ 0 | termination: False, with x as certificate |
| `split` | neither; HI − LO is above the resolution 2⁻²⁰; the event carries the specifications of two children | decomposition |
| `return` | after its split; True when both children returned True, False when a child returned False | back up |

The children are the same criterion and the same ontology with other constants (PATH, LO, HI and
the ancestors). The criterion of the parent admits the split only if the carried specifications are
exactly these specializations, and τ_root then admits them as specifications (R1): the decomposition
is judged by the authority of the parent, not decided by Z₀. Below the resolution an undecided node
stays Not Yet.

## 3. Abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `templates` | once, the specifications of the root node as data | exactly those specifications | own |
| `n` and every node brought in | certify, find a witness, split, or return | the table above | own, `templates`, its two children, its ancestors |

The criterion reads its children through positive atoms only: "a child returned True", "a child
returned False with this witness". With SHORT = true (this system) a node returns False as soon as
one child has, and a node whose ancestor is decided stops (its ontology proposes nothing).

## 4. What it shows

* **Specialization as decomposition.** 91 splits bring in 182 new abstractions; with the root, 183
  nodes. 92 leaves are certified, 91 returns carry the verdict up, and the root returns True.
* **The shape is set by the criterion.** Nodes split only where the bound cannot yet certify, near
  x = 1/3. The number of splits per level grows by about √2 per level, as ε^−1/2: the exponent is
  1 − 1/k for contact of order k. [`split-quartic`](../split-quartic/DESIGN.md) tests the prediction
  for k = 4.

## 5. Expected end

280 events; the root returns True. R2 replays the record; by workers, one per node, every lineage has
the same history.

## 6. Run

```bash
python -m ztes run experiments/e6-decomposition/split
python experiments/run.py e6
```
