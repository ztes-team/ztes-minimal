"""[C] The record as the model reads it: a prefix Cⁿ and its index.        Paper: S1.1, §3.2.5, §9.1

The model never writes C and never sees a store. It reads a prefix Cⁿ through this view:

    Record   a read-only sequence of the first n events (C[:k] is again a view, without copying)
    Index    the positions of the events, so that a binding over the horizon does not scan C

An event is ⟨coord, payload⟩ (§3.2.5). The view relies only on these coordinate fields:
kind ("genesis" | "spec" | "exec"), abstraction, and for specifications role and addr.
How events are made and appended is the business of Z₀ (ztes.substrate); the substrate
builds one Index while it reads the store and hands the model views that share it.

C is append-only (S1.1), so an event once read never changes, and one Index serves every
prefix: each query takes a prefix length n and uses only the events at positions < n.
"""
import bisect
import heapq
import itertools
from collections.abc import Sequence


class Index:
    """[C] Positions of the events of C, built once per event as C is read.

        exec      lineage → (positions, payloads) of its execution events      (phase 3)
        spec_at   address → (position, payload) of an admitted specification    (phases 1, 2;
                  and a specification carried by an execution event, at that event)
        versions  (abstraction, role) → [(position, address)] of its versions  (S1.3)
        maps      incremental entries of "select": "map" bindings  (epistemic.bind)
        memo      other values derived from C once and reused: the horizons (substrate.lookups),
                  the events that pass a filter reading only x (epistemic._qualifying)
    """

    def __init__(self):
        """An empty index: no event read yet."""
        self.exec, self.spec_at, self.versions = {}, {}, {}
        self.maps, self.memo = {}, {}

    def add(self, n, e):
        """Index event e at position n: an execution event under its lineage, a specification under its
        address and among the versions of its abstraction and role. Called once per event, in order.
        The specifications an execution event carries (its coordinate lists them) are indexed as
        specifications admitted at its position, exactly as a specification event would be.
        """
        c = e["coord"]
        if c["kind"] == "exec":
            pos, pay = self.exec.setdefault(c["abstraction"], ([], []))
            pos.append(n)
            pay.append(e["payload"])
            if "carries" in c:
                field = c["carries"]["field"]
                for k, d in enumerate(c["carries"]["specs"]):
                    self.spec_at[d["addr"]] = (n, e["payload"][field][k])
                    self.versions.setdefault((d["abstraction"], d["role"]), []).append((n, d["addr"]))
        elif c["kind"] == "spec":
            self.spec_at[c["addr"]] = (n, e["payload"])
            self.versions.setdefault((c["abstraction"], c["role"]), []).append((n, c["addr"]))

    # ---- execution events of a horizon (the inputs of bindings) ----

    def payloads(self, lineages, n):
        """Payloads of the execution events of the lineages before position n, in record order."""
        return [p for _, p in self.items_between(lineages, 0, n)]

    def items_between(self, lineages, lo, hi):
        """(position, payload) of the execution events of the lineages with lo ≤ position < hi, in order."""
        parts = []
        for a in lineages:
            pos, pay = self.exec.get(a, ((), ()))
            i, k = bisect.bisect_left(pos, lo), bisect.bisect_left(pos, hi)
            parts.append(list(zip(pos[i:k], pay[i:k])))
        return parts[0] if len(parts) == 1 else list(heapq.merge(*parts))

    def count(self, lineages, n):
        """Number of execution events of the lineages before position n."""
        return sum(bisect.bisect_left(self.exec.get(a, ((), ()))[0], n) for a in lineages)

    def last(self, lineages, n):
        """Payload of the latest execution event of the lineages before position n, or None."""
        best = None
        for a in lineages:
            pos, pay = self.exec.get(a, ((), ()))
            k = bisect.bisect_left(pos, n)
            if k and (best is None or pos[k - 1] > best[0]):
                best = (pos[k - 1], pay[k - 1])
        return None if best is None else best[1]

    # ---- admitted specifications (S1.3) ----

    def version_addrs(self, abstraction, role, n):
        """Addresses of the admitted versions of one specification before position n, in order."""
        return [addr for pos, addr in self.versions.get((abstraction, role), ()) if pos < n]

    def spec(self, address, n):
        """The specification admitted at an address before position n, or None."""
        hit = self.spec_at.get(address)
        return hit[1] if hit and hit[0] < n else None


class Record(Sequence):
    """[C] A prefix Cⁿ: a read-only view of the first n events, sharing one Index.

    Taking a prefix C[:k] makes a new view without copying events, so the prefixes used by
    Z₀, by the services and by the replay cost O(1) each and all query the same index.
    """

    def __init__(self, events, n=None, index=None):
        """A view of the first n events of `events` (all of them if n is None), queried through `index`."""
        self._events, self._n, self.index = events, len(events) if n is None else n, index

    def __len__(self):
        """n: the length of the prefix."""
        return self._n

    def __getitem__(self, i):
        """An event of the prefix by position, or a prefix C[:k], which is again a view sharing the index;
        any other slice is a plain list.
        """
        if isinstance(i, slice):
            start, stop, step = i.indices(self._n)
            if start == 0 and step == 1:
                return Record(self._events, stop, self.index)
            return [self._events[k] for k in range(start, stop, step)]
        if i < 0:
            i += self._n
        if not 0 <= i < self._n:
            raise IndexError("record index out of range")
        return self._events[i]

    def __iter__(self):
        """The events of the prefix, in order."""
        return itertools.islice(self._events, self._n)

    def __eq__(self, other):
        """Two prefixes are equal when they hold the same events in the same order."""
        return list(self) == list(other)

    def __repr__(self):
        """Record(n events)."""
        return f"Record({self._n} events)"

    @classmethod
    def of(cls, events):
        """A view of a plain list of events, with its index built now (for tests and tools)."""
        events = list(events)
        ix = Index()
        for n, e in enumerate(events):
            ix.add(n, e)
        return cls(events, len(events), ix)


def indexed(C):
    """The index of a prefix: shared if C is a Record, built now for a plain list of events."""
    if isinstance(C, Record) and C.index is not None:
        return C.index
    return Record.of(C).index
