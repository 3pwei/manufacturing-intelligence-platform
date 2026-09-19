# Advanced Tableau Analytics

## Scope

PR #13 extends the three-dashboard PR #12 workbook with parameter-driven metrics, meaningful LOD
benchmarks, contribution calculations, and an investigation path:

```text
Executive Overview → Manufacturing Quality → Root Cause Analysis
```

The packaged workbook uses only sanitized embedded extracts derived from Gold. No Bronze, Silver,
live Databricks connection, hostname, warehouse path, user identity, token, or credential is
included.

## Interactive investigation

### Executive Overview

- Metric Selector switches FPY, Defect Rate, DPPM, Rework Rate, and Scrap Rate.
- Benchmark Selector switches Overall, Factory, and Product FPY reference.
- Selecting the FPY trend passes the active scope to Manufacturing Quality.
- Use the workbook dashboard tabs to open Manufacturing Quality after the filter selection.

### Manufacturing Quality

- Selected Metric, benchmark, variance, and status support comparison at Factory/Product/Line.
- FIXED Factory/Product benchmarks prevent the lower-level marks from changing the reference.
- EXCLUDE Line retains the parent Product reference during line drill-down.
- Selecting Product Comparison passes the active scope to Root Cause Analysis; use the dashboard
  tab to open the target dashboard.

### Root Cause Analysis

- Defect Pareto highlights related Component/Supplier/Defect marks on hover.
- INCLUDE Component Contribution adds component detail at the contribution grain and aggregates it
  back to the displayed parent view.
- Filter actions use shared business dimensions; no cross-grain physical join is introduced.

## Product-mix scenario (Incident E)

Use Factory `FAC-MX`, May–June 2026:

1. Executive Overview shows aggregate FPY declining.
2. Set Metric Selector to FPY and Benchmark Selector to Product.
3. Manufacturing Quality shows within-product FPY remaining approximately stable.
4. Compare Product Mix Share: X100 volume/share falls while normally lower-yield X200 rises.
5. Classify the aggregate change as a **mix effect**, not broad manufacturing deterioration.

The workbook recomputes product FPY from pass/fail quantities and mix share from production
quantity. It does not average stored daily rates.

## Dashboard actions

| Type | Source | Target | Trigger |
|---|---|---|---|
| Filter | Executive `Trend - FPY` | Manufacturing Quality | Select |
| Filter | Quality `Product Comparison` | Root Cause Analysis | Select |
| Highlight | RCA `Defect Pareto` | RCA contributor sheets | Hover |

## Validation notes

Automated package validation confirms:

- the `.twbx` ZIP and both embedded synthetic Hyper extracts are intact;
- exactly two list parameters exist with the required members;
- FIXED, INCLUDE, and EXCLUDE formulas exist and use additive inputs;
- filter and highlight actions reference existing dashboards/sheets;
- only the two sanitized Gold-derived extracts are packaged;
- sensitive connection markers are absent.

Manual Tableau Desktop verification before publication:

1. Open `tableau/manufacturing_intelligence_advanced_analytics.twbx` in Tableau Desktop 2024.2+
   and accept the compatibility prompt only if shown.
2. Exercise every parameter member and confirm mark values/formatting.
3. Verify context-filter behavior for Factory/Product benchmarks.
4. Follow the dashboard tabs after each filter action and verify the selected scope is retained.
5. Run Incident A–E paths; Incident E must be described as product mix.
6. Capture refreshed screenshots after visual QA, then republish from the owner account.

Publication remains a manual account action. Do not replace the current public workbook until all
six checks pass.
