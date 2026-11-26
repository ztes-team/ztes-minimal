# A tour of the package

For a reader of the paper who wants to see the calculus run. Section, theorem and table numbers
refer to version 4 of the base paper; [`glossary.md`](glossary.md) gives the terms of the paper next
to those printed here (the paper calls the local outcome Not Yet *Pending*), and
[`REPRODUCING.md`](../REPRODUCING.md) lists every result of the paper with its command. It takes four stops: one invocation
followed from start to finish, the map from the paper to the code, the examples in order, and what
happens when a condition is left out. The [README](../README.md) is the reference of the substrate
and [`writing-a-system.md`](writing-a-system.md) the guide for writing a system; this document
only shows the way.

Everything below can be reproduced with

```bash
pip install -r requirements.txt
python -m ztes run examples/sqrt2 --trace
```

## 1. One invocation of Axiom 0

`sqrt2` approximates √2 by bisection. It has two abstractions. `lower` proposes the midpoint of the
current interval when the midpoint is below √2, `upper` when it is above. Each has two
specifications, which are data:

```json
lower/ontology.v1    {"m": "(lower + upper) / 2", "result": "m if m * m < 2 else None"}
lower/criterion.v1   {"result": "w * w < 2 and lower < w < upper"}
```

The ontology says what can be proposed; the criterion says what is admitted. Neither mentions the
other (D2). `lower` and `upper` in these expressions are bindings: the latest admitted value of
each lineage, read from the record, with defaults 1 and 2.

**Phases 1 and 2** record the four specifications. Nothing is evaluated. After them the record C
has five events: the genesis event and four specification events, each stored under the hash of
its content.

**Phase 3** is Axiom 0. The first two invocations, as `--trace` prints them:

```
C^5   lower   → Not Yet
        binding  lower = 1
        binding  upper = 2
        m = 3/2
        ω = ⊥ (None): Not Yet
C^5   upper   → admitted   ω = 3/2
        binding  lower = 1
        binding  upper = 2
        m = 3/2
        ω = 3/2
        candidate w = 3/2
        τ = True
```

What happened, in the terms of the paper:

| Step | In the paper | Here |
|---|---|---|
| Z₀ reads the prefix | Cⁿ, n = 5 | `read(store)`: five events, checked as a chain while they are read |
| Z₀ finds the active versions | active(Cⁿ), S1.3 | the last admitted ontology and criterion of the abstraction |
| 3a, realization | ω := S_ω(Cⁿ), D1 | the service of `lower` evaluates the ontology on C⁵: 3/2 is not below √2, so ω = ⊥ |
| | Not Yet | τ is not called, nothing is appended; `lower` waits |
| 3a for `upper` | | on the same C⁵ the ontology of `upper` gives 3/2 |
| 3b, judgment | b := S_τ(Cⁿ, ω), D2 | the criterion of `upper` on C⁵ and 3/2: true |
| 3c, append | Cⁿ⁺¹ := Cⁿ ⌢ Rec(i, Cⁿ, ω), S1.5 | one atomic conditional insert at position 5 |

The appended event is

```
coord    n = 5, kind exec, abstraction upper,
         ontology  <address of upper/ontology.v1>,
         criterion <address of upper/criterion.v1>,
         prev      <hash of event 4>
payload  "3/2"
```

The two outcomes show D1 without a selector: both abstractions looked at the same midpoint, and
the record decided which of them had a candidate. The event carries everything a later check
needs: where it stands, which versions produced and judged it, and what was admitted.

**Replay (R2)** uses only the record. For event 5 it takes the prefix C⁵, loads the two
specifications named in the coordinate, evaluates the ontology again, compares the result with the
payload, and evaluates the criterion again. `python -m ztes verify DIR` does this for every event
and reports the first check that fails, with the condition of S1 it protects. With `--judgments`
it skips the ontology and only judges the recorded payload again: faster when the ontologies search,
and enough for R2, but it no longer checks that the payload follows from the record (`replay.py`).

**A governed change (R1)** is the next thing `sqrt2` does. After two admissions the plan records
`lower/criterion.v2` and `upper/criterion.v2`, which also require the interval to be wider than
1/64. They are admitted under τ_root by the same rule and become events 7 and 8. Every later
judgment uses version 2; events 5 and 6 still name version 1 in their coordinates, so replay
judges them as they were judged. The run ends when `lower` proposes 181/128 and its criterion is
false: the lineage is closed.

## 2. From the paper to the code

| In the paper | In the package | Shown by |
|---|---|---|
| the record C, append-only (S1.1) | `substrate/store.py`: one write, `put_if_absent` | `test_concurrent_substrates_do_not_fork` |
| an event ⟨coord, payload⟩, Rec (S1.2, S1.5) | `substrate/events.py` | `test_tampering_is_detected` |
| immutable versions, active(C) (S1.3) | `substrate/lookups.py` | `test_phase2_requires_phase1` |
| retained evidence (S1.4) | the payload of every event; `substrate/replay.py` | `test_lossy_evidence_fails_on_the_stored_candidate_too` |
| Axiom 0; Z₀ (§3.4.1, §3.4.3) | `substrate/z0.py`: `execute` | `test_plan_runs_and_replays` |
| τ_root; governance inside execution (R1) | `substrate/governance.py` | `test_tau_root_checks_the_api`, `test_refusal_names_the_reason` |
| verification replay (R2), Theorem B | `substrate/replay.py`: `verify` | `test_every_example_replays` |
| Theorems C, C′, D: no condition can be dropped | `defects.py` | `test_each_of_the_eight_deviations_is_found_by_replay` |
| contextual resolution (D1); ⊥ | `model/ontological.py`, `model/errors.py` | `prime-witnesses`, `aco` |
| separated admission (D2); total Boolean τ | `model/eschatological.py` | `test_factor_criterion_rejects_a_false_certificate` |
| what a specification reads: κ(C); event horizon (Definition 10) | `model/epistemic.py` | `test_window_reads_only_the_last_k_qualifying_events` |
| S_ω, S_τ variable, Z₀ fixed (§3.4.4, §9.1.1) | `model/` never imports `substrate/` | `test_model_does_not_import_the_substrate` |
| boundary abstraction (§5.2) | `"boundary": true`; `system/sources.py` | `test_aco_draws_are_recorded_and_replay_never_asks_the_source` |
| recorded merges; scheduling is not fixed by Axiom 0 (§5.3) | `system/agenda.py`, `system/resume.py` | `test_an_interrupted_run_continues_to_the_same_record` |
| Theorem K and Corollary 7: nondeterminism is located in the record (§5.3) | `system/workers.py`: one worker per abstraction | `test_every_example_under_random_schedules` |
| non-termination: the classes of Theorem 4 (§6.2) | the termination report of `agenda.py`: terminal, closed, permanent wait, the admission limit | `test_sqrt2_termination_states` |
| structural non-progress and governed repair (§6.3, §6.5, Corollary 9, §8.5) | the diagnosis in the termination report; a `govern` step | `test_dedekind_cut_repair` |
| execution indicators (§6.4, §8.8) | `system/kpi.py`: `profile`, and a `kpi` abstraction per problem | `test_kpi_profile_records_what_the_record_does_not_keep` |
| distributed realization (§9.1.1) | `service.py`: one service per abstraction | `test_separate_microservice_processes` |

Three things the paper discusses are not in the package: diagnosis and governing abstractions with
criteria of their own (every specification is admitted under τ_root), abeyance as a recorded
abstraction (§5.2), and consensus across failing nodes (§9.4).

## 3. The examples, in order

Each adds one thing; `examples/README.md` has the table and a guide by question.

1. **`sqrt2`** is the system of stop 1.
2. **`dedekind-cut`** has three streams and a mistake in its design: one ontology reads the wrong
   lineage. The run ends with that abstraction waiting on a lineage nobody writes, the termination
   report says so, and a governed change repairs the horizon. Nothing recorded before is touched.
3. **`payment`** admits two transfers with the same payload on different grounds, and refuses a
   third. `python -m ztes explain DIR N` shows the ground of each from the record.
4. **`prime-witnesses`** admits 10 = 5 + 5 and not 3 + 7, because 7 is not yet certified when the
   invocation completes. The relation is multivalued; the record resolves it. Under another
   schedule of the workers 7 can be recorded first, and then 3 + 7 is admitted (§8.3;
   [`distribution.md`](distribution.md)).
5. **`factorization`** reuses admitted certificates, so later factorizations are checked, not
   searched for.
6. **`tsp`** does the same at scale: 448 subproblems are computed for three questions that need
   720, and optimality is checked against recorded subproblems.
7. **`tsp-bnb`** lets recorded bounds prune a search tree, and records the proof of optimality.
8. **`aco`** is a heuristic with no random number in it: the trail is the record, evaporation is a
   window over it, and a quota replaces the draw.
9. **`aco-draw`** is the same colony with real draws, each admitted as a boundary event.

Every run ends with a summary: for each abstraction how often it was invoked and admitted, how
often it was at Not Yet because its horizon was incomplete (nothing computed) or because its body
gave no candidate, how often τ refused its candidate, and how it ended. Only admissions are in the
record; the other counts enter it as the `profile` of the KPI step.

## 4. What happens when a condition is left out

```bash
python -m ztes defects
```

runs the ant colony on a sound mechanism and on eight defective ones, one for each essential
condition of S1. Each defect is what an ordinary implementation of the method does without
thinking: evaporation that overwrites a stored tour, a random generator outside the record, a
parameter changed in place, an operator who switches a rule by hand. Replay stops at each of them
and names the check that failed; the table is in the README.

The point of this stop is the one the paper makes with Theorems C and D. The eight conditions are
not a list from which a design may choose. Leave any one out, and either a past judgment can no
longer be reproduced (R2) or a change of the rules has escaped the rules (R1).

The contributions of the paper and the examples that confirm them are mapped in Table 10 of the
paper and in [`REPRODUCING.md`](../REPRODUCING.md#the-contributions-of-table-10).

## Where to go next

- to write a system of your own: [`writing-a-system.md`](writing-a-system.md), and
  `python -m ztes new examples/<name> --abstractions a,b`;
- to see what a specification looks like once recorded: `python -m ztes design examples/tsp --full`;
- to run the abstractions as separate processes: the README, "Deployment as separate microservices";
- to interrupt a run and continue it: `python -m ztes run examples/tsp --record DIR`, stop it, and
  run the same command again.
