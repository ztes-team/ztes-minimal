"""Z₀: the zero-tier execution substrate and the record C it writes.   Paper: §3.4.1, §3.4.3, §9.1, [50]

    store.py       [C]  the medium of C: append-only, one atomic conditional insert     S1.1, §9.1
    events.py      [C]  events ⟨coord, payload⟩ and Rec; hash links                     §3.2.5, S1.2, S1.4, S1.5
    lookups.py     [C]  admitted and active versions, event horizons                    S1.3, Definition 10
    governance.py  [Z₀] τ_root: the criterion that admits specifications                §3.4.1, §4.2.7, R1
    z0.py          [Z₀] Axiom 0: phases 1, 2 and 3; the only writer to C                §3.4.1, §3.4.3
    replay.py      [R2] deterministic verification replay from the record alone        §4.2.6, Theorems B, C′

Z₀ is presupposed, not admitted: it is the same for every system. Everything specific to a
system is in its specifications, which Z₀ records and which the model (ztes.model) evaluates.
The substrate uses the model; the model does not use the substrate.
"""
from .store import CorruptRecord, DiskStore, MemoryStore, NotDurable, RedisStore, read
from .z0 import ADMITTED, FALSE, NOT_YET, UNSPECIFIED, Z0
