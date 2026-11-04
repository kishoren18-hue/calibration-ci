"""Paired comparison of a baseline and a candidate run, with bootstrap significance."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from .metrics import METRICS

DEFAULT_POLICY = {
    # metric: maximum allowed worsening (absolute). Worsening = increase for
    # "lower is better" metrics, decrease for "higher is better".
    "ece": 0.02,
    "brier": 0.01,
    "auroc2": 0.02,
    "accuracy": 0.02,
}


@dataclass
class MetricResult:
    name: str
    baseline: float
    current: float
    delta: float
    worsening: float
    ci_low: float | None
    ci_high: float | None
    threshold: float | None
    regressed: bool
    direction: str


@dataclass
class Comparison:
    n_paired: int
    n_baseline_only: int
    n_current_only: int
    results: list[MetricResult] = field(default_factory=list)

    @property
    def regressed(self) -> bool:
        return any(r.regressed for r in self.results)

    def to_dict(self) -> dict:
        return {
            "n_paired": self.n_paired,
            "n_baseline_only": self.n_baseline_only,
            "n_current_only": self.n_current_only,
            "regressed": self.regressed,
            "metrics": [r.__dict__ for r in self.results],
        }

    def markdown(self) -> str:
        icon = "❌ Calibration regression" if self.regressed else "✅ Calibration OK"
        lines = [f"### {icon}", "",
                 f"{self.n_paired} paired items"
                 + (f" ({self.n_baseline_only} only in baseline, {self.n_current_only} only in current)"
                    if self.n_baseline_only or self.n_current_only else ""),
                 "", "| metric | baseline | current | change | 95% CI of worsening | allowed | status |",
                 "|---|---|---|---|---|---|---|"]
        for r in self.results:
            ci = f"[{r.ci_low:+.3f}, {r.ci_high:+.3f}]" if r.ci_low is not None else "n/a"
            thr = f"{r.threshold:.3f}" if r.threshold is not None else "info"
            status = "regressed" if r.regressed else ("ok" if r.threshold is not None else "")
            better = "lower" if r.direction == "lower" else "higher" if r.direction == "higher" else ""
            lines.append(f"| {r.name}{' (' + better + ' is better)' if better else ''} | {r.baseline:.3f} | "
                         f"{r.current:.3f} | {r.delta:+.3f} | {ci} | {thr} | {status} |")
        return "\n".join(lines)


def load_jsonl(path: str | Path) -> dict[str, tuple[int, float]]:
    """Read {id, correct, confidence} rows; returns id -> (correct, confidence)."""
    out = {}
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        try:
            y, p = int(bool(row["correct"])), float(row["confidence"])
        except KeyError as e:
            raise ValueError(f"{path}:{n}: missing field {e}") from None
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"{path}:{n}: confidence {p} outside [0, 1]")
        key = str(row.get("id", n))
        if key in out:
            raise ValueError(f"{path}:{n}: duplicate id {key!r}")
        out[key] = (y, p)
    if not out:
        raise ValueError(f"{path}: no rows")
    return out


def _metric(name, y, p):
    return METRICS[name][0](y, p)


def compare(baseline: dict, current: dict, policy: dict | None = None, n_boot: int = 1000,
            alpha: float = 0.05, require_significance: bool = True, seed: int = 0,
            info_metrics=("overconfidence",)) -> Comparison:
    """Compare two runs on their shared item ids.

    A metric regresses when its observed worsening exceeds the policy threshold
    and, if require_significance, the bootstrap CI of the worsening lies above 0.
    The significance check stops flaky failures on small eval sets.
    """
    policy = DEFAULT_POLICY if policy is None else policy
    ids = sorted(set(baseline) & set(current))
    if len(ids) < 10:
        raise ValueError(f"only {len(ids)} shared item ids; need at least 10")
    yb = [baseline[i][0] for i in ids]
    pb = [baseline[i][1] for i in ids]
    yc = [current[i][0] for i in ids]
    pc = [current[i][1] for i in ids]
    cmp = Comparison(len(ids), len(set(baseline) - set(current)), len(set(current) - set(baseline)))
    rng = random.Random(seed)
    boot_idx = [[rng.randrange(len(ids)) for _ in ids] for _ in range(n_boot)] if n_boot else []

    for name in list(policy) + [m for m in info_metrics if m not in policy]:
        if name not in METRICS:
            raise ValueError(f"unknown metric {name!r}; choose from {sorted(METRICS)}")
        direction = METRICS[name][1]
        b, c = _metric(name, yb, pb), _metric(name, yc, pc)
        sign = 1 if direction == "lower" else -1 if direction == "higher" else 0
        worsening = sign * (c - b)
        lo = hi = None
        if boot_idx and sign:
            ws = []
            for idx in boot_idx:
                bb = _metric(name, [yb[k] for k in idx], [pb[k] for k in idx])
                cc = _metric(name, [yc[k] for k in idx], [pc[k] for k in idx])
                if not (math.isnan(bb) or math.isnan(cc)):
                    ws.append(sign * (cc - bb))
            ws.sort()
            if ws:
                lo = ws[int(alpha / 2 * len(ws))]
                hi = ws[min(int((1 - alpha / 2) * len(ws)), len(ws) - 1)]
        thr = policy.get(name)
        regressed = bool(thr is not None and sign and worsening > thr
                         and (not require_significance or lo is None or lo > 0))
        cmp.results.append(MetricResult(name, b, c, c - b, worsening, lo, hi, thr, regressed, direction))
    return cmp
