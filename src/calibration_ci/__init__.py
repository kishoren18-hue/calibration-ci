"""calibration-ci: regression tests for model confidence."""

from .compare import DEFAULT_POLICY, Comparison, MetricResult, compare, load_jsonl
from .metrics import METRICS, accuracy, auroc2, brier, ece, overconfidence

__version__ = "0.2.0"
