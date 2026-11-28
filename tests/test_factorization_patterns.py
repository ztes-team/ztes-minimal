"""Check the published factorization experiment and the completeness of its probe evidence."""

from copy import deepcopy
import gzip
import json
import os
import subprocess
import sys

from conftest import ROOT
from ztes.substrate.replay import verify


MODEL = ROOT / "examples" / "computability" / "factorization-patterns"


def load_records(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def test_native_fixture_regenerates_published_records(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(ROOT), env.get("PYTHONPATH"))))
    subprocess.run([sys.executable, str(MODEL / "experiment.py"), "--output", str(tmp_path)],
                   env=env, check=True)
    records = load_records(tmp_path / "records.json.gz")
    assert records == load_records(MODEL / "results" / "records.json.gz")
    assert set(records) == {"parity", "fresh", "reuse", "no_trigger"}
    summary = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert summary == json.loads((MODEL / "results" / "results.json").read_text(encoding="utf-8"))
    counts = {mode: [len(t["probes"]) for t in run["targets"]]
              for mode, run in summary["runs"].items()}
    assert counts == {"parity": [3, 6, 1], "fresh": [3, 4, 1], "reuse": [3, 4, 1]}
    control = summary["no_trigger"]
    assert [(r["n"], r["factors"], r["probes"]) for r in control["targets"]] == [
        (1457, [31, 47], [39]),
        (2929, [29, 101], [55, 57, 59, 61, 63, 65]),
    ]
    assert len(records["no_trigger"]) == 23
    for attempts in (control["attempts"], control["attempts_after_target"]):
        calls = attempts["calls"]
        assert [call["lineage"] for call in calls] == ["diagnosis", "pattern", "activate"]
        assert all(call["outcome"] == "Not Yet" and call["events_added"] == 0 for call in calls)
    # Only the source can be diagnosed: the target's failed probes leave the record terminal for governance.
    assert control["attempts_after_target"]["prefix_events"] == len(records["no_trigger"])
    assert set(summary["faults"]) == {"incomplete_mask", "dangling_plan_reference", "obsolete_plan_version",
                                      "wrong_signature"}
    assert all(row["path"] == "parity" for row in control["targets"])


def test_probe_criterion_rejects_omitting_a_failed_target_probe():
    record = load_records(MODEL / "results" / "records.json.gz")["reuse"]
    index = next(i for i, e in enumerate(record) if e["coord"]["kind"] == "exec"
                 and e["coord"]["abstraction"] == "probes" and e["payload"]["n"] == 2929)
    trial = deepcopy(record[:index + 1])
    observation = trial[-1]["payload"]
    assert observation["centers"] == [55, 57, 63, 65]
    observation["centers"].pop(1)
    observation["differences"].pop(1)
    # The successful center and all remaining arithmetic are still correct.
    errors = verify(trial, judgments_only=True)
    assert len(errors) == 1 and errors[0][0] == index and "criterion is false" in errors[0][1]
