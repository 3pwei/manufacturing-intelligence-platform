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

## Visual sign-off

Tableau Desktop visual/interaction sign-off and replacement of the three Tableau Public views are
required after PR review. This file deliberately does not claim that automated XML inspection can
replace Desktop rendering and interaction testing.
