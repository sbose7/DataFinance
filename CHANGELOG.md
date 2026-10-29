# Changelog

## 0.2.0 — 2026-10-29

### Added
- `project`: multi-year hold projection with rent and expense growth, appreciation, loan paydown, sale, IRR, equity multiple, and CSV export.
- `brrrr`: one-pass acquisition, rehab, refinance, and rental analysis.
- `sensitivity`: two-variable grid over any input (dotted paths for projection assumptions) and any output metric.
- `compare`: rank several deals of the same kind side by side.
- `serve`: local web app with live verdicts, stress-test heatmap, projection chart, and pinned-deal comparison.
- `amortize --csv`.
- `finance` module with NPV and IRR.

### Changed
- CLI output is generated from a shared formatter, so every analysis prints every metric.
- JSON output replaces infinite values (e.g. cash-on-cash with no cash in) with `null`.

## 0.1.0 — 2026-10-29

- Initial release: rental, flip, and refinance analysis, amortization schedules.
