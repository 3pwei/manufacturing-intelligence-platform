# PR #13 Workbook Validation

Artifact: `tableau/manufacturing_intelligence_advanced_analytics.twbx`

## Automated result

`PASS` — package integrity, XML parsing, parameter membership, metric-aware Overall/Factory/Product
benchmarks for all five metrics, three LOD types, calculated-field presence, dashboard-action
presence, embedded-extract allowlist, and sensitive-marker scan.

## Data boundary

The package contains only:

- sanitized workbook XML;
- `gold_manufacturing_daily` synthetic extract;
- `gold_defect_pareto` synthetic extract.

It contains no live Databricks metadata or credentials.

## Automated validation layers

### Pull request / CI

Run `pytest`. The workbook contract tests inspect the packaged TWBX and fail on broken XML,
missing parameter members, incorrect metric/benchmark wiring, invalid dashboard worksheet
references, incomplete Apply to Worksheets scope, unsafe connections, unsupported mark encodings,
and the layout regressions already found during PR #13 review.

The existing Databricks Tableau validation job remains responsible for Gold data contracts and
Incident A–E assertions. Incident E separately asserts declining aggregate FPY, approximately
stable product-level FPY, and a product-mix shift.

### After Tableau Public publication

Run the GitHub Actions workflow **Tableau Public validation** and provide the published URLs for
the three dashboards. It opens every view in Chromium, rejects Tableau error pages and missing
render surfaces, exercises two Metric/Benchmark URL-parameter scenarios, and uploads screenshots
plus `report.json` as a 14-day workflow artifact.

This workflow is deliberately manual-dispatch because publishing is an owner-account action and a
pull request cannot know the final published revision URL.

## Remaining manual sign-off

Only these steps remain manual:

1. Open the TWBX once in Tableau Desktop and confirm there is no warning or automatic sheet removal.
2. Publish/replace the Tableau Public workbook from the owner account.
3. Review the uploaded browser screenshots for final spacing, clipping, scrollbars, color legends,
   and readability.

Clicks and dropdown changes no longer need to be exhaustively repeated by hand: their workbook
wiring is checked in CI, while the published-render smoke test checks that the resulting views load.
