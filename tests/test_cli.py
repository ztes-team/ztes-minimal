"""The command line and the services: run, verify, new, trace, explain, serve, HTTP."""
import json
import shutil

import pytest
from pathlib import Path

from conftest import FACTOR, SQRT2, quiet
from ztes.__main__ import main
from ztes.system.system import System
from ztes.substrate.store import DiskStore, read
from ztes.substrate.replay import verify


def test_command_line(tmp_path, capsys):
    assert main(["run", str(SQRT2), "--record", str(tmp_path)]) == 0
    assert main(["verify", str(tmp_path)]) == 0
    assert "R2  replay of 16 events: OK" in capsys.readouterr().out
    assert main(["verify", str(tmp_path), "--judgments"]) == 0
    assert "R2  replay of 16 events (judgments only: the candidates are not re-derived): OK" in capsys.readouterr().out


def test_a_failing_specification_stops_the_run_with_its_location(tmp_path, capsys):
    bad = tmp_path / "bad"
    shutil.copytree(SQRT2, bad)
    f = bad / "abstractions" / "upper" / "ontology.v1.json"
    s = json.loads(f.read_text())
    s["body"]["result"] = "[m][1] if m * m > 2 else None"         # IndexError at run time
    f.write_text(json.dumps(s))
    assert main(["run", str(bad), "--record", str(tmp_path / "rec")]) == 2
    out = capsys.readouterr().out
    assert "upper/ontology.v1, body 'result': IndexError" in out


def test_new_creates_a_valid_skeleton(tmp_path, capsys):
    root = tmp_path / "mine"
    assert main(["new", str(root), "--abstractions", "alpha,beta"]) == 0
    system = System(root)
    assert system.check(log=quiet) == []
    store = DiskStore(tmp_path / "rec")
    system.run(store, log=quiet)
    assert system.states(read(store)) == {"alpha": "wait", "beta": "wait"}
    assert "## 2. Decomposition into binary relations" in (root / "DESIGN.md").read_text()


def test_trace_shows_bindings_and_steps(tmp_path):
    lines = []
    System(SQRT2).run(DiskStore(tmp_path), log=lines.append, trace=True)
    text = "\n".join(lines)
    assert "binding  lower = 1" in text and "m = 3/2" in text and "τ = True" in text


def test_explain_shows_the_ground_of_an_event(tmp_path, capsys):
    from ztes.system.report import explain_event
    store = DiskStore(tmp_path)
    System(SQRT2).run(store, log=quiet)
    lines = []
    explain_event(read(store), 5, log=lines.append)
    text = "\n".join(lines)
    assert "event 5: exec of upper" in text and "ω = 3/2" in text and "τ = True" in text


def test_http_services_carry_json_candidates(tmp_path):
    """Regression: over HTTP the candidate travels as JSON, so integers and records keep their type."""
    from fastapi.testclient import TestClient
    from ztes.service import HttpService, make_app
    system = System(FACTOR)
    store = DiskStore(tmp_path)
    services = {a: HttpService(client=TestClient(make_app(store, a))) for a in system.abstractions}
    system.run(store, services, log=quiet)
    C = read(store)
    assert verify(C) == [] and len(C) == 27


def test_separate_microservice_processes(tmp_path):
    """Each abstraction in its own `serve` process, sharing the record with the process that runs Z₀."""
    import socket, subprocess, sys, time
    import httpx
    rec = tmp_path / "rec"
    ports = {}
    for a in ("lower", "upper"):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            ports[a] = s.getsockname()[1]
    procs = [subprocess.Popen([sys.executable, "-m", "ztes", "serve", str(SQRT2), a, "--port", str(p),
                               "--record", str(rec)], cwd=Path(__file__).parent.parent)
             for a, p in ports.items()]
    try:
        for a, p in ports.items():
            for _ in range(100):
                try:
                    if httpx.get(f"http://127.0.0.1:{p}/health").json() == {"abstraction": a}:
                        break
                except httpx.HTTPError:
                    time.sleep(0.1)
        urls = tmp_path / "services.json"
        urls.write_text(json.dumps({a: f"http://127.0.0.1:{p}" for a, p in ports.items()}))
        assert main(["run", str(SQRT2), "--record", str(rec), "--services", str(urls)]) == 0
        assert verify(read(DiskStore(rec))) == []
    finally:
        for p in procs:
            p.terminate()
            p.wait()


def test_run_writes_metrics_as_json(tmp_path, capsys):
    out = tmp_path / "kpi.json"
    assert main(["run", str(SQRT2), "--record", str(tmp_path / "C"), "--metrics", str(out)]) == 0
    kpi = json.loads(out.read_text())
    assert kpi["system"] == "sqrt2" and kpi["states"] == {"lower": "closed", "upper": "wait"}
    assert sum(r["I"] for r in kpi["abstractions"]) == 10 and kpi["record"]["exec"]["events"] == 7   # 6 + profile
    assert "KPI  (I invocations" in capsys.readouterr().out


def test_a_silent_service_is_asked_again_and_then_given_up(tmp_path):
    """3a and 3b write nothing, so a failed call is repeated; Z₀ never waits without limit."""
    import httpx
    from ztes.service import HttpService, ServiceUnavailable
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if len(calls) < 3:
            raise httpx.ConnectTimeout("no answer", request=request)
        return httpx.Response(200, json={"omega": 7})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://a")
    assert HttpService(client=client, retries=2).realize("addr", 3) == 7 and len(calls) == 3
    calls.clear()
    dead = httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=r))),
                        base_url="http://a")
    with pytest.raises(ServiceUnavailable, match="ReadTimeout"):
        HttpService(client=dead, retries=1).judge("addr", 3, 7)
