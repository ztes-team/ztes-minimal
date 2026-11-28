# The same cases under a pruning planner

The cases of `scaling`, with one constant changed: the planner extends a plan only if the checker refused it as short, since a refusal for priority, undecided or negative holds for every extension. The fresh search tests 3, 6, 10 and 15 complete plans for k = 2 … 5. A reused plan still costs one proof in the ontology and one in the criterion: the work of a derivation is that of the planner version, the cost of a reuse is not. [Design of the thread](../DESIGN.md)
