"""Reproduce the Goldbach experiment and check evidence that remains valid across its regimes."""

from copy import deepcopy
import gzip
import json
from math import isqrt
import os
import runpy
import subprocess
import sys

import pytest

from conftest import ROOT
from ztes.substrate.replay import verify


MODEL = ROOT / "examples" / "computability" / "goldbach-governed-convolution"
ARCHIVE = MODEL / "results" / "records.json.gz"


def load_records(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def test_all_archived_goldbach_runs_regenerate(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(ROOT), env.get("PYTHONPATH"))))
    subprocess.run([sys.executable, str(MODEL / "experiment.py"), "--output", str(tmp_path)],
                   env=env, check=True)
    records = load_records(tmp_path / "records.json.gz")
    assert records == load_records(ARCHIVE)
    assert set(records) == {"unchanged", "governed_reuse", "governed_fresh", "no_trigger"}
    summary = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert summary == json.loads((MODEL / "results" / "results.json").read_text(encoding="utf-8"))
    runs = summary["runs"]
    assert runs["unchanged"]["queries"][1]["count"] == 4
    for mode in ("governed_reuse", "governed_fresh"):
        assert runs[mode]["queries"][1]["pairs"] == [[7, 13], [13, 7], [17, 3]]
    assert runs["no_trigger"]["queries"][0]["pairs"] == [[2, 2]]
    assert runs["no_trigger"]["queries"][1]["count"] == 4
    assert runs["no_trigger"]["activation_attempt"]["outcome"] == "Not Yet"
    after = runs["no_trigger"]["activation_after_evidence"]
    assert after["admissible"] is True and after["answer_ref"] == "answer/2" and after["events_added"] == 0
    assert after["prefix_length"] == len(records["no_trigger"])


@pytest.mark.parametrize("fault", ["unqueried_coefficient", "missing_witness", "obsolete_right_source"])
def test_tampered_successor_evidence_is_refused_at_its_own_event(fault):
    record = load_records(ARCHIVE)["governed_reuse"]
    lineage = "answer" if fault == "missing_witness" else "product"
    matching = [i for i, e in enumerate(record) if e["coord"]["kind"] == "exec"
                and e["coord"]["abstraction"] == lineage]
    first, successor = matching
    prefix = deepcopy(record[:successor + 1])
    retained = prefix[-1]["payload"]
    if fault == "unqueried_coefficient":
        # No query requests 4 here, but the product must certify the whole vector.
        assert retained["counts"][4] == 1 and retained["counts"][20] == 3
        retained["counts"][4] = 0
    elif fault == "missing_witness":
        retained["pairs"].remove([17, 3])
        retained["count"] = len(retained["pairs"])
    else:
        obsolete = prefix[first]["payload"]["right_ref"]
        assert obsolete != retained["right_ref"]
        retained["right_ref"] = obsolete
    errors = verify(prefix, judgments_only=True)
    assert len(errors) == 1 and errors[0][0] == successor and "criterion is false" in errors[0][1]


def test_transform_grid_rules_out_aliasing_and_short_order():
    valid_grid = runpy.run_path(str(MODEL / "native" / "lib.py"), init_globals={"isqrt": isqrt})["valid_grid"]
    assert valid_grid(20, 64, 257, 3)
    assert not valid_grid(20, 32, 257, 3)     # e.g. the input term 19+19 would wrap to index 6
    assert not valid_grid(20, 64, 257, 256)   # -1 mod 257 has order two
