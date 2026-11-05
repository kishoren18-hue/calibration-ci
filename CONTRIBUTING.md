# Contributing to calibration-ci

Thanks for your interest in improving calibration-ci. Bug reports, ideas, documentation fixes and code are all welcome.

## Getting set up

```bash
git clone https://github.com/kishoren18-hue/calibration-ci
cd calibration-ci
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install        # optional: lint on every commit
```

Run the checks CI runs:

```bash
ruff check .
pytest --cov=calibration_ci
```

## Making a change

1. Open an issue first for anything larger than a small fix, so we can agree on the approach.
2. Create a branch, make the change, and add or update tests.
3. Keep pull requests focused on one thing; describe what changed and why.
4. Make sure the checks above pass, then open a pull request.

Good tests matter more than clever code here. A bug fix should come with a test that fails without the fix.

## Ideas to start with

Issues labeled [good first issue](https://github.com/kishoren18-hue/calibration-ci/labels/good%20first%20issue) are scoped for a first pull request, with the files to touch and what "done" means. Other ideas:

* Add adaptive (equal-count) ECE as an optional metric
* Support CSV input in addition to JSONL
* Add a per-slice breakdown (e.g. by task category) to the report

## Code of conduct

By participating you agree to follow the [code of conduct](CODE_OF_CONDUCT.md).
