# Synthetic Incident Specification

The generator will create a stable baseline plus known incidents. Each incident must be reproducible and detectable by expected analytical evidence.

| Incident | Hidden root cause | Visible symptom | Expected finding |
|---|---|---|---|
| A — Supplier degradation | Supplier B Power Module quality worsens for selected lots | FPY falls and voltage defects rise | Supplier B + Power Module explains a large share of incremental failures |
| B — Test calibration | Mexico test station drifts out of calibration | Sudden voltage/test failures on one line | Failure concentration is line/station-specific, not broad supplier deterioration |
| C — Line ramp-up | New production line has learning-curve instability | Higher rework and modest FPY drop | New line underperforms established lines and improves over time |
| D — Bad component lot | A narrow component lot is defective | Sharp localized defect spike | Lot-level concentration dominates component failures |
| E — Product mix shift | Production shifts toward a normally lower-yield product | Aggregate FPY declines | Within-product FPY stays stable; weighted mix explains aggregate movement |

## Design requirements

For every implemented incident define:
- start/end period;
- affected factory, line, product, component, supplier, and lot where relevant;
- effect size;
- symptom exposed in dashboards;
- hidden root cause;
- expected SQL/Tableau/AI conclusion;
- regression-test tolerance.

The data must contain ambiguity and competing signals, but the planted root cause must remain statistically discoverable.
