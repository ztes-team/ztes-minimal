"""[ω][τ] An abstraction as a microservice: the boundary between Z₀ and the model.   Paper: §3.4.4, §9.1.1

One service per abstraction. It holds no domain logic and no durable state: in phase 3 Z₀
names a specification address and a prefix length n; the service reads Cⁿ (read-only),
loads that specification from the record, evaluates it with the model (realize for step 3a,
judge for step 3b), and returns the result. It never writes to C.

Changing what an abstraction does means admitting a new specification
version (phases 1 or 2), not redeploying the service (§4.2.7).
"""
import time

from .model import SpecError, judge, realize
from .substrate import lookups
from .substrate.store import read


class ServiceUnavailable(Exception):
    """An abstraction service gave no answer on Cⁿ within its limits; nothing was appended."""


class AbstractionService:
    """wait: how many seconds the service waits until its store holds Cⁿ. A service that reads
    a replica may be behind the primary; it then waits, and never answers on a shorter prefix.
    A lagging replica costs time and nothing else: it is not Not Yet, which is a fact of Cⁿ.
    """

    def __init__(self, store, name, wait=0.0):
        """The service of abstraction `name`, reading the record in `store`."""
        self.store, self.name, self.wait = store, name, wait

    def _load(self, address, n):
        """Exactly the prefix Cⁿ, and the specification at `address`, which must be admitted in it and
        belong to this abstraction. A store that holds fewer than n events is waited for, up to `wait`
        seconds; then ServiceUnavailable.
        """
        until = time.monotonic() + self.wait
        while len(C := read(self.store, n)) != n:       # exactly the prefix Cⁿ on which Z₀ judges
            if time.monotonic() >= until:
                raise ServiceUnavailable(f"{self.name}: the store read here holds {len(C)} events, not C^{n}")
            time.sleep(0.005)
        s = lookups.load(C, address)                    # only admitted specifications can be evaluated
        if s["abstraction"] != self.name:
            raise ValueError("the specification belongs to another abstraction")
        return C, s

    def realize(self, address, n, occurrence=None):
        """Step 3a [ω]: Sω(Cⁿ) → ω or None (⊥); for a boundary abstraction, the bound occurrence."""
        C, s = self._load(address, n)
        return realize(C, s, occurrence)

    def judge(self, address, n, w):
        """Step 3b [τ]: Sτ(Cⁿ, ω) → true or false."""
        C, s = self._load(address, n)
        return judge(C, s, w)


def make_app(store, name, wait=0.0):
    """The same service exposed over HTTP (FastAPI): GET /realize and POST /judge.

    The candidate ω is any JSON value (integer, "p/q", record, list), so /judge takes it
    as JSON in the request body, never as a URL parameter (which would turn it into text).
    """
    from fastapi import Body, FastAPI
    from fastapi.responses import JSONResponse
    svc, app = AbstractionService(store, name, wait), FastAPI(title=f"abstraction {name}")

    @app.exception_handler(ServiceUnavailable)
    def unavailable(request, x):                # e.g. the replica read here does not hold Cⁿ yet
        """A service that cannot read Cⁿ yet answers 503, and the client asks again."""
        return JSONResponse({"unavailable": str(x)}, status_code=503)

    @app.get("/health")
    def health():
        """The name of the abstraction: the service is up."""
        return {"abstraction": name}

    @app.get("/realize")
    def realize(address: str, n: int):
        """Step 3a on Cⁿ: {"omega": ω or null}, or {"error": …} for a defect of the specification."""
        try:
            return {"omega": svc.realize(address, n)}
        except SpecError as x:                  # a defect of the specification, not of the service
            return {"error": str(x)}

    @app.post("/realize")
    def realize_boundary(address: str = Body(), n: int = Body(), occurrence=Body()):
        """Step 3a of a boundary abstraction: the occurrence bound to the invocation, read through its
        specification.
        """
        try:                                    # a boundary abstraction: the occurrence of the invocation
            return {"omega": svc.realize(address, n, occurrence)}
        except SpecError as x:
            return {"error": str(x)}

    @app.post("/judge")
    def judge(address: str = Body(), n: int = Body(), w=Body()):
        """Step 3b on Cⁿ: {"value": true or false}, or {"error": …} for a defect of the specification."""
        try:
            return {"value": svc.judge(address, n, w)}
        except SpecError as x:
            return {"error": str(x)}

    return app


class HttpService:
    """Client the substrate Z₀ uses when an abstraction runs as a separate process.

    Steps 3a and 3b read Cⁿ and write nothing, so a call that fails in transport is simply made
    again: `retries` more times, each within `timeout` seconds. So is a call the service
    declined (503) because the replica it reads does not hold Cⁿ yet. If the service still does not
    answer, the invocation ends with ServiceUnavailable and nothing is appended; Z₀ never waits
    without limit and never guesses a judgment.
    """

    def __init__(self, url=None, client=None, timeout=10.0, retries=2):
        """A client for the service at url (or the given httpx client): `timeout` seconds for each call,
        and `retries` more attempts.
        """
        if client is None:
            import httpx
            client = httpx.Client(base_url=url, timeout=timeout)
        self.http, self.retries = client, retries

    def _call(self, method, path, **kw):
        """One request, made again after a failure in transport or an answer 503, up to `retries` times;
        then ServiceUnavailable.
        """
        import httpx
        for attempt in range(self.retries + 1):
            try:
                r = getattr(self.http, method)(path, **kw)
                if r.status_code != 503:
                    return r.json()
                why = r.json().get("unavailable", "503")
            except httpx.TransportError as x:
                why = f"{type(x).__name__}: {x}"
            if attempt == self.retries:
                raise ServiceUnavailable(f"{method.upper()} {path}: {why}")

    @staticmethod
    def _answer(r, key):
        """The value under `key` of an answer. A defect of the specification reported by the service is
        raised here as SpecError, as in process.
        """
        if "error" in r:
            raise SpecError(r["error"])
        return r[key]

    def realize(self, address, n, occurrence=None):
        """Step 3a over HTTP (AbstractionService.realize); a boundary abstraction sends its occurrence."""
        if occurrence is not None:
            body = {"address": address, "n": n, "occurrence": occurrence}
            return self._answer(self._call("post", "/realize", json=body), "omega")
        return self._answer(self._call("get", "/realize", params={"address": address, "n": n}), "omega")

    def judge(self, address, n, w):
        """Step 3b over HTTP (AbstractionService.judge); the candidate travels as JSON."""
        return self._answer(self._call("post", "/judge", json={"address": address, "n": n, "w": w}), "value")
