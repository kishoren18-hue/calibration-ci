"""calibration-ci command line.

    calibration-ci compare --baseline evals/baseline.jsonl --current evals/current.jsonl
    calibration-ci report evals/current.jsonl

Exit codes: 0 ok, 1 calibration regression, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .compare import DEFAULT_POLICY, compare, load_jsonl
from .metrics import METRICS


def load_config(path: str | None) -> dict:
    if not path:
        default = Path("calibration-ci.toml")
        if not default.exists():
            return {}
        path = str(default)
    text = Path(path).read_text()
    if path.endswith(".json"):
        return json.loads(text)
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11
        try:
            import tomli as tomllib
        except ModuleNotFoundError:
            raise SystemExit("TOML config needs Python 3.11+ or `pip install tomli`; or use a .json config") from None
    return tomllib.loads(text)


def cmd_compare(a) -> int:
    cfg = load_config(a.config)
    opts = cfg.get("options", {})
    policy = cfg.get("thresholds", DEFAULT_POLICY)
    try:
        base, cur = load_jsonl(a.baseline), load_jsonl(a.current)
        res = compare(
            base, cur, policy=policy,
            n_boot=int(a.boot if a.boot is not None else opts.get("n_boot", 1000)),
            require_significance=not a.no_significance and opts.get("require_significance", True),
            seed=int(opts.get("seed", 0)),
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    md = res.markdown()
    print(md)
    if a.json:
        Path(a.json).write_text(json.dumps(res.to_dict(), indent=2))
    if a.markdown:
        Path(a.markdown).write_text(md + "\n\n<sub>Posted by calibration-ci</sub>\n")
    if a.svg:
        from .diagram import reliability_svg
        shared = sorted(set(base) & set(cur))
        Path(a.svg).write_text(reliability_svg({
            "baseline": ([base[i][0] for i in shared], [base[i][1] for i in shared]),
            "current": ([cur[i][0] for i in shared], [cur[i][1] for i in shared]),
        }))
    summary = a.summary or os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(md + "\n")
    if res.n_baseline_only or res.n_current_only:
        print(f"\nwarning: item sets differ; compared {res.n_paired} shared ids", file=sys.stderr)
    return 1 if res.regressed else 0


def cmd_report(a) -> int:
    try:
        data = load_jsonl(a.path)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    y = [v[0] for v in data.values()]
    p = [v[1] for v in data.values()]
    print(f"n = {len(y)}")
    for name, (fn, direction) in METRICS.items():
        print(f"{name:<15} {fn(y, p):.4f}" + (f"   ({direction} is better)" if direction != "info" else ""))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="calibration-ci", description="Fail CI when model calibration regresses.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="compare a candidate run against a baseline")
    c.add_argument("--baseline", required=True)
    c.add_argument("--current", required=True)
    c.add_argument("--config", help="TOML or JSON policy file (default: ./calibration-ci.toml if present)")
    c.add_argument("--boot", type=int, help="bootstrap resamples (0 disables significance testing)")
    c.add_argument("--no-significance", action="store_true", help="fail on any worsening above threshold")
    c.add_argument("--json", help="write machine-readable results here")
    c.add_argument("--summary", help="append the markdown table to this file")
    c.add_argument("--markdown", help="write the markdown table to this file (e.g. for a PR comment)")
    c.add_argument("--svg", help="write a baseline-vs-current reliability diagram (SVG) here")
    c.set_defaults(func=cmd_compare)
    r = sub.add_parser("report", help="print metrics for one run")
    r.add_argument("path")
    r.set_defaults(func=cmd_report)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
