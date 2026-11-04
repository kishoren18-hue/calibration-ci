import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from calibration_ci import auroc2, brier, compare, ece, load_jsonl
from calibration_ci.cli import main

EX = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture(scope="session", autouse=True)
def examples():
    subprocess.run([sys.executable, str(EX / "make_examples.py")], check=True, capture_output=True)


def test_metrics_known_values():
    y, p = [1, 1, 0, 0], [0.9, 0.8, 0.3, 0.1]
    assert brier(y, p) == pytest.approx((0.01 + 0.04 + 0.09 + 0.01) / 4)
    assert auroc2(y, p) == 1.0
    assert auroc2([1, 0], [0.5, 0.5]) == 0.5
    assert ece([1, 0], [1.0, 0.0]) == 0.0


def test_auroc2_matches_bruteforce():
    rng = random.Random(1)
    y = [rng.randint(0, 1) for _ in range(200)]
    p = [round(rng.random(), 1) for _ in range(200)]  # many ties
    pos = [pi for yi, pi in zip(y, p) if yi]
    neg = [pi for yi, pi in zip(y, p) if not yi]
    brute = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg))
    assert auroc2(y, p) == pytest.approx(brute)


def test_harmless_change_passes():
    res = compare(load_jsonl(EX / "baseline.jsonl"), load_jsonl(EX / "current_ok.jsonl"), n_boot=300)
    assert not res.regressed


def test_overconfidence_is_caught():
    res = compare(load_jsonl(EX / "baseline.jsonl"), load_jsonl(EX / "current_regressed.jsonl"), n_boot=300)
    assert res.regressed
    failed = {r.name for r in res.results if r.regressed}
    assert "ece" in failed
    assert "accuracy" not in failed


def test_significance_prevents_flaky_failure_on_tiny_sets():
    rng = random.Random(3)
    base = {str(i): (rng.randint(0, 1), rng.random()) for i in range(20)}
    cur = {k: (y, min(1.0, p + rng.uniform(-0.1, 0.15))) for k, (y, p) in base.items()}
    strict = compare(base, cur, policy={"ece": 0.0}, n_boot=300, require_significance=False)
    lenient = compare(base, cur, policy={"ece": 0.0}, n_boot=300, require_significance=True)
    assert strict.regressed or not lenient.regressed  # significance can only make it more lenient
    assert not lenient.regressed


def test_cli_exit_codes(tmp_path):
    assert main(["compare", "--baseline", str(EX / "baseline.jsonl"),
                 "--current", str(EX / "current_ok.jsonl"), "--boot", "200"]) == 0
    out = tmp_path / "r.json"
    assert main(["compare", "--baseline", str(EX / "baseline.jsonl"),
                 "--current", str(EX / "current_regressed.jsonl"), "--boot", "200", "--json", str(out)]) == 1
    assert json.loads(out.read_text())["regressed"] is True
    assert main(["compare", "--baseline", "nope.jsonl", "--current", "nope.jsonl"]) == 2


def test_cli_reads_toml_config(tmp_path):
    cfg = tmp_path / "policy.toml"
    cfg.write_text('[thresholds]\naccuracy = 0.05\n\n[options]\nn_boot = 100\n')
    # with only an accuracy threshold, the overconfident run passes
    assert main(["compare", "--baseline", str(EX / "baseline.jsonl"),
                 "--current", str(EX / "current_regressed.jsonl"), "--config", str(cfg)]) == 0


def test_bad_rows_rejected(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"id": "a", "correct": 1, "confidence": 1.4}\n')
    with pytest.raises(ValueError, match="outside"):
        load_jsonl(f)
    f.write_text('{"id": "a", "correct": 1, "confidence": 0.4}\n{"id": "a", "correct": 0, "confidence": 0.4}\n')
    with pytest.raises(ValueError, match="duplicate"):
        load_jsonl(f)


def test_pytest_fixture(calibration):
    calibration.check(EX / "baseline.jsonl", EX / "current_ok.jsonl", n_boot=200, ece=0.02)
