"""pytest integration. Installing the package registers a `calibration` fixture:

    def test_calibration_holds(calibration):
        calibration.check("evals/baseline.jsonl", "evals/current.jsonl", ece=0.02, auroc2=0.03)
"""

from __future__ import annotations

import pytest

from .compare import DEFAULT_POLICY, compare, load_jsonl


class CalibrationChecker:
    def check(self, baseline, current, n_boot: int = 1000, require_significance: bool = True, **thresholds):
        policy = thresholds or DEFAULT_POLICY
        b = load_jsonl(baseline) if not isinstance(baseline, dict) else baseline
        c = load_jsonl(current) if not isinstance(current, dict) else current
        res = compare(b, c, policy=policy, n_boot=n_boot, require_significance=require_significance)
        if res.regressed:
            pytest.fail("calibration regressed\n\n" + res.markdown(), pytrace=False)
        return res


@pytest.fixture
def calibration() -> CalibrationChecker:
    return CalibrationChecker()
