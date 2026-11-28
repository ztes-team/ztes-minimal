"""Integration of the model's domain tests, experimental records and native specifications."""

import gzip
import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT


MODEL = ROOT / "examples" / "computability" / "structural-memoization"


def run_model(*args):
    # Run the standalone module names in a separate interpreter that uses this checkout of ZTES.
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(ROOT), env.get("PYTHONPATH"))))
    subprocess.run([sys.executable, *args], cwd=MODEL, env=env, check=True)


@pytest.mark.parametrize("suite", ["test_cases", "test_planner", "test_governance"])
def test_model_regressions(suite):
    run_model("-m", "unittest", "-v", suite)


def test_published_executions_replay_and_can_be_reproduced(tmp_path):
    archive = MODEL / "results" / "records.json.gz"
    run_model("experiment.py", "--verify", str(archive))
    run_model("experiment.py", "--pairs", "1", "--series-pairs", "1", "--output", str(tmp_path))
    # Timings depend on the host. All admitted events, including the governed versions, are deterministic.
    with gzip.open(archive, "rt", encoding="utf-8") as saved:
        published = json.load(saved)
    with gzip.open(tmp_path / "records.json.gz", "rt", encoding="utf-8") as fresh:
        regenerated = json.load(fresh)
    assert len(published) == 13
    assert regenerated == published


def test_native_files_match_export(tmp_path):
    run_model("experiment.py", "--export-systems", str(tmp_path))
    native = MODEL / "native"
    paths = {p.relative_to(native) for p in native.rglob("*") if p.is_file() and p.suffix != ".pyc"}
    emitted = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file() and p.suffix != ".pyc"}
    assert emitted == paths
    for path in sorted(paths):
        assert (tmp_path / path).read_text(encoding="utf-8") == (native / path).read_text(encoding="utf-8"), path
