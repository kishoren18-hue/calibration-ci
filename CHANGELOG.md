# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-04

### Added

- Optional pull request comment with the results table (updated in place)
- Baseline-vs-current reliability diagram (SVG) and JSON uploaded as a workflow artifact
- `--svg` and `--markdown` CLI outputs; TOML config on Python < 3.11 via tomli
- Contributor docs, issue templates, linting and coverage in CI, release workflow

## [0.1.0] - 2026-11-04

### Added

- Paired comparison of ECE, Brier, type-2 AUROC and accuracy with bootstrap CIs
- Composite GitHub Action, CLI with exit codes, pytest `calibration` fixture
