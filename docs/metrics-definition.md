# Metric Definitions

Canonical definitions are governed contracts. Tableau and AI outputs must not silently redefine them.

| Metric | Definition | Default grain / notes |
|---|---|---|
| Production Quantity | completed units in analysis scope | Sum at selected dimensional grain |
| Pass Quantity | units passing defined quality criterion | Scope must state first-pass vs final pass |
| Fail Quantity | units failing first-pass criterion | Do not double count repeated defect events |
| First Pass Yield (FPY) | first_pass_pass_qty / (first_pass_pass_qty + fail_qty) | Weighted by units; not average of subgroup percentages |
| Defect Rate | defective units / inspected units | Unit-based unless explicitly event-based |
| DPPM | defective units / inspected units × 1,000,000 | Same unit deduplication rules as Defect Rate |
| Rework Rate | rework_qty / completed_qty | Selected reporting period |
| Scrap Rate | scrap_qty / completed_qty | Selected reporting period |
| Yield Loss | 1 - FPY | Percentage or percentage points must be labeled clearly |
| Defect Contribution | failures attributable to selected defect / total failures | Used for Pareto / RCA |
| Factory Benchmark | FPY calculated at factory grain regardless of lower-level view | Intended Tableau FIXED LOD use case |
| Product Benchmark | FPY calculated at product grain regardless of line/component detail | Benchmark use case |
| WoW FPY Change | current-week FPY - previous-week FPY | Express in percentage points |
| Supplier-attributed Defect Rate | defective attributable units / inspected units linked to supplier | Attribution caveat required |

## Required metadata for new metrics

Every new metric must specify business definition, formula, numerator, denominator, grain, applicable filters, null behavior, and known caveats.

## Aggregation rule

Rates are recomputed from additive numerators and denominators whenever possible. Do not average pre-aggregated percentages across groups unless the business definition explicitly requires it.
