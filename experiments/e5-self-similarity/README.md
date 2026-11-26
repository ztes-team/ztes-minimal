# E5. Self-similarity of the record of a recursion

*Experiment E5 of [`experiments/README.md`](../README.md). It has no system of its own: it runs the
specifications of [`e3-recursion/ackermann-deep`](../e3-recursion/ackermann-deep/DESIGN.md) for eight
roots, A(1, 5), A(2, 5), A(2, 13), A(2, 29) and A(3, 2) … A(3, 5), and reads their records.*

**The justification of a value.** The criterion of `value` admits A(m, n) on recorded values only:
none for m = 0, A(m − 1, 1) for n = 0, and A(m, n − 1) = u and A(m − 1, u) otherwise. These are the
positive atoms on which the judgment was true. Following them from a value gives the structure of
its justification, a graph whose nodes are recorded events.

## What is measured

1. **Copies of itself.** For nine pairs, the structure below `value(m, n)` inside a larger record is
   compared with the whole record of A(m, n) run alone: the same values, the same premises.
2. **Growth by doubling.** The record of A(3, n) is compared with the beginning of the record of
   A(3, n + 1), and the distance back in the record at which each judgment reads its premises is
   counted per octave (1, 2–3, 4–7, …).
3. **Dimension.** Between consecutive roots of the series A(3, n): the exponent of the size of the
   record, and of the size of the unfolded justification (what naive recursion would derive again
   and again), as functions of the depth of justification.

## Result

1. All nine pairs are equal: the record contains itself at smaller scales, on three levels of m.
2. Each record is the exact beginning of the next and about twice as long (73, 154, 315, 636
   values). The short reads double with each step, and the farthest read moves one octave further:
   the same pattern at twice the scale.
3. The record grows with exponent 1.05, 1.02, 1.01; the unfolded justification with 2.12, 2.06,
   2.03. The record is a one-dimensional image of a self-similar justification of dimension two.
   The compression is done by the reuse of admitted facts alone.

Self-similarity follows from the recursive definition. What the substrate adds is that the record
keeps it exactly: as equality of substructures, as a prefix, and in the same order under every
schedule (E3). The exponents are measured on four roots, not proved.

```bash
python experiments/run.py e5
```
