# An absorbing quantum walk on four nodes: the model (step 0)

*Not an example of the paper. Three systems on the same Z₀: `bright`, `dark`, `dephasing`.
Base paper: Theorem 4, Proposition 14, Corollary 9. Tags: [C] epistemic, [ω] ontological,
[τ] eschatological (see [`examples/README.md`](../../README.md)).*

**What this model adds.** Theorem 4 in a physical system. A quantum walk on four nodes, one of them
attached to an absorbing trap, gives three outcomes:
* from one start, every goal of the family below is attained at a finite step, class 𝔒;
* from another start, half of the walk never reaches the trap. A certificate admitted in the record
  shows that most goals are unreachable at every prefix, class 𝔓;
* a compensation event, admissible only once that certificate is recorded, adds dephasing and
  makes those goals reachable again (§6.5, Corollary 9).

The mechanism is a dark state: a part of the walk that interference keeps away from the trap
forever. A classical random walk on the same graph is absorbed with probability 1.

**A bridge to the theory of algorithms and to transport.** A quantum walk can have an infinite
hitting time, which a classical walk on a finite connected graph cannot. The cause is a degeneracy
of the step operator, which comes from a symmetry of the graph (Krovi and Brun, Phys. Rev. A 74,
042334, 2006). Here the step has the eigenvalue 1 twice. In models of excitation transfer, dephasing
noise can open pathways that destructive interference closes. This is dephasing-assisted transport
(Plenio and Huelga, New J. Phys. 10, 113019, 2008; Caruso, Chin, Datta, Huelga and Plenio, J. Chem.
Phys. 131, 105106, 2009, where the invariant subspaces are identified).

**What it does not claim.**
* It is not a model of a light-harvesting complex, which has more sites, site energies and a
  thermal environment.
* It makes no claim about how much coherence contributes to transfer in nature (see
  [`../path-sums/DESIGN.md`](../path-sums/DESIGN.md)).
* In this small model the classical limit is about as fast as moderate dephasing, so the model shows
  the dark state and its removal, not an optimal level of noise.
* It adds no computational power (§4.5 of the paper): it executes a standard exact discrete-time
  evolution.

## 1. The walk

The graph is a square, with nodes 1, 2, 3, 4 and edges 1–2, 1–3, 2–4, 3–4. Node 1 is coupled to
the trap. A is the adjacency matrix. One step is the Crank–Nicolson form of the continuous-time walk
e^(−iAt) with Δt = 2/3:

    U = (I + iA/3)⁻¹ (I − iA/3) = 1/13 · [[ 9, −6i, −6i, −4],
                                          [−6i,  9,  −4, −6i],
                                          [−6i, −4,   9, −6i],
                                          [ −4, −6i, −6i,  9]]

U is exactly unitary and has the eigenvectors of A. The eigenvalues of A are 2, 0, 0 and −2, so
those of U are (5 − 12i)/13, 1, 1 and (5 + 12i)/13. The Pythagorean triple 5–12–13 plays the role
that 3–4–5 plays in `path-sums`.

The state at step t is a density matrix ρₜ. A pure state would suffice without dephasing, but
dephasing needs ρ. One step applies three maps in turn:
1. **Unitary.** ρ ↦ UρU†.
2. **Dephasing with strength q.** ρ ↦ (1 − q)ρ + q·diag(ρ): every off-diagonal entry is multiplied
   by 1 − q. This is a which-site detector that fires with probability q; like the detector of
   `two-slits`, it labels the walk and cuts nothing.
3. **Absorption.** The probability at node 1 is added to `absorbed`, and row and column 1 are set
   to 0.

Every entry is a Gaussian integer over the integer `den` = 13^(2t)·4^s, where s is the number of
steps with q > 0. The criterion checks that each step before absorption keeps the trace, so the
trace plus `absorbed` stays 1 exactly. Time is the step t, a value of the model; ZTES has no time
([`../path-sums/DESIGN.md`](../path-sums/DESIGN.md), §1).

## 2. Goals, and what the specifications decide

The family of goals is G_k: "a slice with absorbed ≥ 1 − 2⁻ᵏ is recorded", k = 1, 2, … . Each goal
is persistent: `absorbed` never decreases, and the record only grows.

**The dark state.** Nodes 2 and 3 have the same neighbours, so d = e₂ − e₃ satisfies Ad = 0 and
hence Ud = d, and d is 0 at node 1. Let P remove node 1. With q = 0 every step leaves ⟨d|ρ|d⟩
unchanged: ⟨d|PUρU†P|d⟩ = ⟨d|ρ|d⟩, because Pd = d and U†d = d. The probability that never reaches
the trap is therefore at least ⟨d|ρ|d⟩/2 at every step.

* **`dark`, start at node 2.** ⟨d|ρ₀|d⟩/2 = 1/2, so absorbed ≤ 1/2 at every prefix of every
  continuation of the regime. G_k is False for every k ≥ 2, already at the first prefix: class 𝔓.
  The bound is an inductive invariant in the sense of Proposition 14: it holds at the first slice,
  every admitted step keeps it, and it excludes G₂.
* **`bright`, start at node 4.** The component along d is 0 and stays 0. Restricted to the
  complement of d, the step with absorption has the eigenvalues 0 and (7 ± 2√17·i)/13, with
  |λ|² = 9/13. An eigenvalue of modulus 1 would need an eigenvector of U that is 0 at node 1, and
  the only such vector is d. The probability that remains falls roughly as (9/13)ᵗ, so every G_k
  is attained at a finite step. The specification has no bound, so the unbounded execution is in 𝔒.
  This is an unconditional 𝔒, unlike `collatz`.
* **`dephasing`, start at node 2.** Under q = 0 the certificate of `dark` is admitted. A
  compensation event, admissible only once that certificate is recorded, then activates q = 1/4 at
  slice 20. Dephasing shrinks ρ₂₃, the coherence that keeps the dark state, so the invariant fails,
  and every G_k becomes reachable. Let Sₜ be the probability that remains after step t. After a
  step with dephasing, ρₜ = (1 − q)·PσₜP + q·P diag(σₜ)P, where σₜ is the state before dephasing and
  both terms are positive semidefinite, so at least the share q of Sₜ is diagonal. From node 2, 3
  or 4 one step moves at least |U₁ⱼ|² ≥ 16/169 of a diagonal state to the trap. Hence
  Sₜ₊₁ ≤ (1 − 16q/169)·Sₜ, which is (165/169)·Sₜ for q = 1/4 from t = 21 on, and Sₜ → 0: every
  threshold 1 − 2⁻ᵏ is crossed at a finite step. This is Corollary 9: G₂ is reached along a governed
  history, at slice 30, although no continuation of the earlier regime reaches it. Every judgment
  before the change still replays (R2).
* **The classical limit, q = 1.** The diagonal then follows a Markov chain with transition
  probabilities |U_ij|², which are 81, 36, 36 and 16 out of 169. From every start it is absorbed
  with probability 1. A test checks this; no system records it.

| System | Start | q | What the record shows | Class of the unbounded execution |
|---|---|---|---|---|
| `bright` | node 4 | 0 | G_k attained one by one | 𝔒 |
| `dark` | node 2 | 0 | an admitted certificate: absorbed ≤ 1/2 forever | 𝔓 |
| `dephasing` | node 2 | 0, then 1/4 | the certificate, the compensation event that it makes admissible, then G_k attained | 𝔓 under q = 0; after the change every G_k is reached along the governed history (Corollary 9) |

`dark` and `bright` differ only in the constant START, the node of slice 0. In `finish-unfair` and
`finish-unreachable` the specification of `policy` differs and the payloads are equal. Here the
rules of the walk are the same, and the start decides the class.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology: what it proposes | [τ] Criterion: what it admits | [C] Horizon |
|---|---|---|---|---|
| `step` | Step | the next slice from the last recorded one; slice 0 from START | it equals one step exactly (U, then dephasing with Q, then absorption); trace + absorbed = 1; 0 ≤ Q ≤ 1 | `step` |
| `certificate` | Unreach | if Q = 0: a pair of nodes other than node 1 with the same neighbours, d = eᵢ − eⱼ with ⟨d\|ρ₀\|d⟩ > 0 for the start ρ₀; the dark probability p = ⟨d\|ρ₀\|d⟩/2, the bound 1 − p, and the least k with 1 − 2⁻ᵏ > 1 − p; ⊥ if there is none | Ud = d exactly, with the U of its own regime; d is 0 at node 1; Q = 0; p is recomputed from the start; k is the least such k | `certificate` |
| `compensation` (`dephasing` only) | – | when a certificate is recorded and the walk waits at slice 20: a decision that carries `step` and `certificate` v2, with Q = 1/4; ⊥ before, and after its decision | the authority in force: one decision, only after a certificate, from the slice at which the walk waits; it carries only the four specifications of `step` and `certificate`, with Q equal to the q it states, 0 < q ≤ 1 | `step`, `certificate`, itself |
| `kpi` | – | the slices and certificates recorded, the first slice of each G_k, absorbed and the dark probability at the last slice | each equals its definition | all |

Payload of a slice: `{"t": 7, "diag": [n₂, n₃, n₄], "off": [[re, im]₂₃, [re, im]₂₄, [re, im]₃₄],
"absorbed": n, "den": 13¹⁴}`, every numerator over `den`. Node 1 is not stored, since it is 0 after
absorption. Payload of a certificate: `{"pair": [2, 3], "dark": "1/2", "bound": "1/2", "k": 2}`.
D·U is a derived value, computed once from A, ε and D by `cayley()` in `lib.py`.

**D2: the ontology searches, the criterion checks**, as in `machines`. The criterion checks the
certificate against the step operator and the start of its own regime, not against the slices
recorded so far; it reads no slice, so its horizon is its own lineage. That is why it is a claim
about every continuation (§10 of the paper: unreachability needs its own argument, and its admission
is replayed). In `bright` the ontology finds the pair (2, 3), but p = 0, so it proposes nothing:
`certificate` stays ⊥, and no certificate is needed.

## 4. Design decisions

* **Crank–Nicolson, not e^(−iAt).** Every value is exact, so R2 replays bit for bit. The step has the
  eigenvectors of A, so the dark state is that of the continuous-time walk.
* **A density matrix**, because dephasing is not a unitary map.
* **An unbounded step and a window in the plan**, as in `collatz`. The classes concern the unbounded
  execution, and the record is a window of it. A `step` with a bound T would make every execution
  terminal and empty the question.
* **The trap removes probability and records it**, as the screen of `two-slits` does (`absorbed`).
  One trap is enough.
* **Four nodes.** On three nodes, either there is no dark state (the path with the trap at an end),
  or every start other than the trap keeps a dark part (the path with the trap in the middle, and
  the triangle). The square is the smallest graph on which one start is half dark and another is
  completely bright.
* **The certificate is an admitted event** (Proposition 14). The evidence for 𝔓 is in the record,
  and R2 replays its admission at its own prefix. It reads the regime, not the slices, because it
  is a claim about every continuation. Without it, a window of slices with absorbed < 1/2 would
  show only that no goal is attained yet.
* **A compensation admitted in execution** (R1, §6.5 of the paper). The certificate is an admitted
  diagnosis; it makes `compensation` due, whose decision carries the change Δ, `step` and
  `certificate` v2 with Q = 1/4. Its criterion is the authority in force: it admits the change only
  when the record holds a certificate, so the proof that the earlier regime cannot reach G₂ governs
  what happens next. The walk continues from the recorded slice 20, and nothing is recomputed.
* **The walk waits for the decision.** In `dephasing`, `step` v1 proposes nothing after slice 20
  until `compensation` has decided, and `compensation` waits for the certificate. Every abstraction
  then has the same history under every schedule (`docs/writing-a-system.md`, specifications carried
  by a candidate). `step` and `certificate` change together, because a regime changes as a whole.

## 5. Plan

```
bright      phase 1, phase 2; phase 3, a window of 41 admissions (slices 0 … 40); kpi
dark        phase 1, phase 2; phase 3, a window of 42 admissions (slices 0 … 40 and the certificate); kpi
dephasing   phase 1, phase 2; phase 3, a window of 63 admissions (the certificate, slices 0 … 20,
            the decision of compensation, slices 21 … 60); kpi
```

`certificate` reads only the regime (A, START, Q), so it is enabled from the first prefix, and the
agenda admits it before slice 0. In `dark`, under workers, it can be admitted at another position of
the window, or after it. In `dephasing` the waits make the history of every abstraction that of the
agenda under every schedule. There is no `govern` step: the change is an admitted event.

## 6. Expected end

| System | Slices | Certificate | Absorbed at the last slice | First slice of G₁, G₂, … |
|---|---|---|---|---|
| `bright` | 41 | none | 0.99999957 | 2, 5, 6, 9, 10, 13, 14, 16, 17, 20, 21, 24, … |
| `dark` | 41 | (2, 3), p = 1/2, G_k unreachable for k ≥ 2 | 0.49999981, below 1/2 at every slice | none |
| `dephasing` | 61 | (2, 3), before the change at slice 20 | 0.9915 | 22, 30, 36, 42, 49, 55 |

The records have 52, 53 and 76 events with the KPI step, and R2 replays each. The run computes
these values, and the tests check them against an independent computation.

## 7. Tests (`tests/test_absorbing.py`)

| Test | Checks |
|---|---|
| `test_absorbing_example_is_well_formed_and_meets_its_expected_end` | `check` passes; the run meets `"expect"` |
| `test_absorbing_example_replays_in_process_and_over_http` | R2; the same record with every abstraction as an HTTP service |
| `test_every_slice_equals_an_independent_exact_computation` | every slice of the three systems equals a computation written apart from `lib.py`; trace + absorbed = 1 |
| `test_the_step_is_the_crank_nicolson_form_and_unitary` | (I + iA/3)·U = I − iA/3 and U·U† = I for the U of §1, exactly |
| `test_dark_keeps_half_of_the_walk_from_the_trap_at_every_slice` | ⟨d\|ρ\|d⟩/2 = 1/2 at every slice; absorbed < 1/2; the certificate |
| `test_a_wrong_certificate_is_refused_and_dephasing_admits_none` | D2: the pair (2, 4), a pair with the trap, a wrong bound or k are refused; a pair of another length gives false, not an error; under Q = 1/4 the ontology proposes nothing |
| `test_bright_the_step_with_absorption_has_no_other_eigenvalue_of_modulus_1` | λ(λ − 1)(13λ² − 14λ + 9) = 0 for PU, exactly; d is the eigenvector of 1; each G_k of the window at its first slice |
| `test_dephasing_restores_reachability_after_the_governed_change` | Corollary 9: the certificate, then the compensation at slice 20 carrying the four specifications; absorbed < 3/4 at slice 29 and ≥ 3/4 at slice 30; slices 0 … 20 equal those of `dark` |
| `test_dephasing_remaining_probability_falls_by_at_least_165_169_per_step` | Sₜ₊₁ ≤ (165/169)·Sₜ at every slice from t = 21 on |
| `test_the_compensation_is_admissible_only_after_a_certificate` | without a certificate the walk waits at slice 20 and nothing changes; a decision with another q, without all four specifications, or from another slice is refused |
| `test_with_q_1_the_walk_is_a_classical_markov_chain` | the diagonal follows the chain \|U_ij\|² exactly, no coherence, absorbed > 99 % |
| `test_a_wrong_digit_a_step_that_is_not_unitary_or_a_strength_outside_0_1_is_refused` | a changed numerator is refused; a directed edge makes U non-unitary, refused at slice 1; Q = 5/4 is refused at slice 0 |

The general tests (pinned records, both replay modes, every store, workers) cover these systems as
they cover `path-sums`.

## 8. Not in this step

* The continuous-time walk e^(−iAt), whose values are not rational.
* A light-harvesting complex: more sites, site energies, a thermal environment, and noise that is
  not Markovian.
* An optimal level of noise.
* Quantum search with a marked node, for example on the hypercube (Krovi and Brun).

## 9. Files

```
DESIGN.md         this design of the model
bright/           start at node 4: system.json, lib.py, DESIGN.md, abstractions/{step, certificate, kpi}
dark/             start at node 2: the same rules of the walk
dephasing/        start at node 2, then a compensation event carrying Q = 1/4: abstractions/compensation,
                  and step and certificate v2 (named in the constant CHANGE, not recorded by the plan)
```

Every system is self-contained, so each repeats the helpers of the walk in its own `lib.py`.
