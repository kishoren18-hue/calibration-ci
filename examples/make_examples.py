"""Generate example eval runs: a baseline, a harmless change, and a regression.

The regressed run keeps accuracy the same but becomes overconfident, the kind
of change an accuracy-only test suite would never catch.
"""

import json
import math
import random
from pathlib import Path

rng = random.Random(42)
here = Path(__file__).parent
N = 500

items = []
for i in range(N):
    logit = rng.gauss(0.8, 1.4)
    p_true = 1 / (1 + math.exp(-logit))
    items.append((f"q{i:04d}", p_true, int(rng.random() < p_true)))


def write(name, conf_fn, flip=0.0):
    with open(here / name, "w") as f:
        for qid, p, y in items:
            yy = 1 - y if rng.random() < flip else y
            f.write(json.dumps({"id": qid, "correct": yy, "confidence": round(conf_fn(p), 4)}) + "\n")


clip = lambda v: min(max(v, 0.01), 0.99)  # noqa: E731
write("baseline.jsonl", lambda p: clip(p + rng.gauss(0, 0.05)))
write("current_ok.jsonl", lambda p: clip(p + rng.gauss(0, 0.06)))
# overconfident: push every confidence toward 1
write("current_regressed.jsonl", lambda p: clip(1 - (1 - p) * 0.35 + rng.gauss(0, 0.03)))
print("wrote baseline.jsonl, current_ok.jsonl, current_regressed.jsonl")
