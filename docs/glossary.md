# Terms of the papers and of the repository

This page gives the terms the repository uses next to those of the papers. Most terms are the
same. Where they are not, the repository keeps its own name, because that name is part of its output
and of recorded payloads, and this page gives the correspondence.

Two papers use this repository:

* **the base paper**: *A Calculus of Execution for Interacting Binary Relations* (Škarić, Ivanović,
  M. Radenković, Prokhorov, Labus, B. Radenković), Preprints 2026, 2026081545, version 4,
  https://doi.org/10.20944/preprints202608.1545.v4. Every section, theorem, corollary and table
  number in this repository refers to version 4 of this paper.
* **the companion paper**: *Observable, Governable, Cooperative: Execution Analytics and Adaptive
  Heuristic Agents in the OEE Calculus* (M. Radenković, Prokhorov, Labus, B. Radenković), in
  preparation. Its examples are in
  [oee-heuristic-agents](https://github.com/ztes-team/oee-heuristic-agents), which uses this
  substrate.

## The record and the two relations

| In the base paper | In this repository | In the code |
|---|---|---|
| the record C, the epistemic axis (S1.1) | the record, C | `substrate/store.py`, `model/view.py` |
| an event ⟨coord, payload⟩ (Definition 2, §3.2.5) | an event of kind `genesis`, `spec` or `exec` | `substrate/events.py` |
| the ontology ω, the proposal relation Ont = graph(ω) (§3.2) | the ontology, Sω; its file `ontology.vN.json` | `model/ontological.py` |
| the criterion τ, the admission relation Γτ⁺, the positive extension of a total Boolean predicate on the preceding prefix and the candidate (§3.2, §3.2.3) | the criterion, Sτ; its file `criterion.vN.json` | `model/eschatological.py` |
| an abstraction A_τ = (R, ω, τ) (§3.2.1) | an abstraction: a directory `abstractions/<name>/` | `system/authoring.py` |
| what a specification reads: κ(C), the event horizon (Definition 10, §5.1) | bindings and the horizon a specification declares | `model/epistemic.py` |
| Axiom 0 and the fixed procedure Z₀ (§3.4.1, §3.4.3) | Z₀; phase 3, steps 3a, 3b, 3c | `substrate/z0.py` |
| the root criterion τ_root (§3.2.1) | τ_root: it admits every specification event | `substrate/governance.py` |
| a governing event; R1 (§1.3, §4.2.7, Corollary 3) | a governed change: the plan step `govern`, or specifications carried by a candidate | `substrate/governance.py`, `docs/specifications-in-execution.md` |
| deterministic verification replay; R2 (§1.3, §4.2.6) | `verify`; the full replay, or `--judgments` | `substrate/replay.py` |
| the self-certifying record (S1.5) | the hash link to the previous event | `substrate/events.py` |
| a boundary abstraction (§5.2) | `"boundary": true`; an occurrence from a declared source | `system/sources.py` |

## The outcome of one invocation

| In the base paper | In this repository | Note |
|---|---|---|
| Completed(ω) and τ(C, ω) = true: an admission | `admitted` | one event is appended |
| Completed(ω) and τ(C, ω) = false | `false`, counted as F; at termination `closed` | a completed refusal; it may be a protective refusal (§6.3) |
| **Pending**: the observation supplied no completed candidate (§3.2.2, §3.4.1) | **Not Yet (ω = ⊥)**, counted as U | the same thing under another name; nothing is appended and τ is not called |
| Pending because a declared input is missing | the part H of U: `horizon` | the body is not evaluated (`"requires"`, §8.8) |
| Pending on a complete horizon | U − H: `body` | the body ran and gave no candidate |
| Pending that persists while the horizon cannot change, at Terminal_r(C) (§4.6.5) | `permanent wait` | a statement about this run, not a proof of unreachability |
| semantic **Not Yet**: a goal absent from the prefix and reachable in some extension (Definition 6, §4.4.8) | not computed by the substrate | in oee-heuristic-agents, `vns-tw` uses Not Yet in this sense for a premature city |

The paper calls the local outcome **Pending** and reserves **Not Yet** for the status of a goal.
The repository prints `Not Yet` for the local outcome, and the KPI of `tsp` names it `tour_not_yet`.
The name stays, because it is part of recorded payloads. Read it as Pending.

## Execution, order and termination

| In the base paper | In this repository | Note |
|---|---|---|
| Axiom 0 does not fix which invocation comes next | the agenda (`central` mode), or a race of workers (`workers` mode) | `system/agenda.py`, `system/workers.py`, `docs/distribution.md` |
| a fixed regime r (§4.4.1) | the specifications active between two governed changes | a governed change starts a new regime |
| Terminal_r(C): no admissible one-step extension (§4.6.5) | `terminal: no abstraction can extend C in this regime` | established exactly, from the declared horizons |
| a run that does not reach Terminal_r | `admission_limit` reached: not terminal | a guard of the realization, not a theorem |
| Lemma 6: a judgment stands while its horizon stands (§5.1) | a lost race outside the horizon is appended one position later | `Z0._stands`, `test_a_lost_race_outside_the_horizon_keeps_the_judgment` |
| Theorem K and Corollary 7: fair executions differ only in recorded merges, boundaries and governing events (§5.3) | the same history of every lineage under every schedule, for results determined by their inputs | `test_every_example_under_random_schedules`; see `docs/distribution.md` for results resolved by context |
| the profile counts n_I, n_A, n_U, n_H, n_F (§8.8) | the `profile` columns I, A, U, H, F | I = A + U + F and 0 ≤ H ≤ U; checked by the criterion of `profile` |

## Terms of the experiments

| Term | Meaning | Where |
|---|---|---|
| positive atom | "an event with this content is in the record": true on a prefix, true on every extension | `experiments/README.md` |
| normal form of a criterion | a criterion that reads other lineages only through positive atoms (and, or, there exists), and its own lineage only for its position and uniqueness | `experiments/README.md`; `docs/writing-a-system.md` |
| justification of a value | the recorded events on which its criterion was true, followed back | experiment E5 |

## The classes of non-termination (Theorem 4, §6.2) in a run

Theorem 4 classifies whole executions relative to the goals of a task. A run of the substrate is
finite, so it shows a finite prefix of an execution, and the classes appear as follows.

| Class | In the base paper | How it appears here |
|---|---|---|
| 𝔗 | terminating solution | the run is terminal and every goal stated in `"expect"` holds |
| 𝔒 | ontological infinity: infinite, and every goal is reached at a finite prefix | an ontology that never refuses, such as the bisection of √2 (§8.2). `sqrt2` executes a finite prefix of it: criterion v2 stops the refinement at width 1/64; `experiments/e7-fates/sqrt2-digits`: a stream of digits whose goal is reached at C^16 |
| 𝔓 | pathological non-progress: a goal has status False at some prefix | `dedekind-cut` with ontology v1 of `intervals`: the run is terminal and `intervals` waits on a lineage nobody writes. A governed change repairs the horizon (Corollary 9, §8.5); `experiments/e4-demand/cycle`: a circular recursion ends quiescent with no value |
| 𝔚 | perpetual Not Yet: no False, and some goal never reached | depends on the schedule and fairness (§5.3); `experiments/e7-fates/goldbach` shows it in a window of observation: a search for a counterexample that no recorded prefix establishes or excludes |

## Tags in the code and in the specifications

| Tag | Meaning |
|---|---|
| `[C]` | the epistemic axis: the record, what is read from it, how it is written |
| `[ω]` | the ontological axis: Sω, realization, ⊥ |
| `[τ]` | the eschatological axis: Sτ, the judgment, exactly one Boolean |
| `[Z₀]` | Z₀, the fixed admission procedure of the zero-tier execution substrate: Axiom 0, τ_root, the only writer to C |
| `[A0]` | one application of Axiom 0: steps 3a, 3b, 3c |
| `[S1.k]`, `[R1]`, `[R2]` | the conditions of S1 and the requirements they secure (§3.3, §4.2) |

## Positions

The software numbers positions in the record from zero; the base paper numbers them from one
(§4.1.2). Position k in the output of `run`, `explain` and `verify` is position k + 1 in the
notation of the paper.
