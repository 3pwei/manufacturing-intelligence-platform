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

## Implemented windows (PR #2)

| ID | Window | Scope | Injected driver |
|---|---|---|---|
| INC-A | 2026-03-15–2026-04-12 | Supplier B / Power Module | supplier-component failure probability |
| INC-B | 2026-04-15–2026-05-05 | Mexico / Line 2 | line-local test risk and Voltage Failure distribution |
| INC-C | 2026-02-01–2026-05-31 | Malaysia / Ramp Line | decaying line risk and early rework propensity |
| INC-D | 2026-05-10–2026-05-16 | Taiwan / X200 / Supplier C memory | `CLOT-BAD-001` failure probability |
| INC-E | 2026-06-01–2026-06-30 | Mexico | X100-to-X200 production mix weights |

Exact settings and expected conclusions are emitted to `ground_truth/incidents.json`. Governed
analytics must never join to or read this manifest; it exists only for regression and future RCA
evaluation.
