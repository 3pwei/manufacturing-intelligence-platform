# Tableau Calculated Fields — Advanced Analytics

Gold remains the metric source of truth. Tableau calculations change presentation grain and
interaction only; rates are always recomputed from additive numerators and denominators.

## Parameters

### Metric Selector

String list: `FPY`, `Defect Rate`, `DPPM`, `Rework Rate`, `Scrap Rate`. Default: `FPY`.

### Benchmark Selector

String list: `Overall`, `Factory`, `Product`. Default: `Factory`.

The benchmark selector applies to the currently selected metric. Every metric has governed
Overall, Factory, and Product FIXED references calculated from the same additive Gold quantities.

## Selected Metric

```tableau
CASE [Metric Selector]
WHEN "FPY" THEN
  SUM([pass_quantity]) / (SUM([pass_quantity]) + SUM([fail_quantity]))
WHEN "Defect Rate" THEN SUM([fail_quantity]) / SUM([production_quantity])
WHEN "DPPM" THEN SUM([fail_quantity]) * 1000000.0 / SUM([production_quantity])
WHEN "Rework Rate" THEN SUM([rework_quantity]) / SUM([production_quantity])
WHEN "Scrap Rate" THEN SUM([scrap_quantity]) / SUM([production_quantity])
END
```

Null denominators remain null. DPPM is formatted as a whole number; every other option is a rate.

## Selected Metric Benchmark

```tableau
CASE [Metric Selector]
WHEN "FPY" THEN
  CASE [Benchmark Selector]
  WHEN "Overall" THEN [Overall FPY Benchmark (FIXED)]
  WHEN "Factory" THEN [Factory FPY Benchmark (FIXED)]
  WHEN "Product" THEN [Product FPY Benchmark (FIXED)] END
WHEN "Defect Rate" THEN
  CASE [Benchmark Selector]
  WHEN "Overall" THEN [Overall Defect Rate Benchmark (FIXED)]
  WHEN "Factory" THEN [Factory Defect Rate Benchmark (FIXED)]
  WHEN "Product" THEN [Product Defect Rate Benchmark (FIXED)] END
// DPPM, Rework Rate, and Scrap Rate follow the same level selection.
END
```

## Variance vs Benchmark

```tableau
[Selected Metric] - [Selected Metric Benchmark]
```

FPY and rate variances display as percentage points; DPPM displays as a whole-number DPPM delta.
For FPY, positive is favorable. For Defect Rate, DPPM, Rework Rate, and Scrap Rate, negative is
favorable.

## Favorable Variance

```tableau
IF [Metric Selector] = "FPY" THEN
  [Variance vs Benchmark]
ELSE
  -[Variance vs Benchmark]
END
```

Positive always means favorable, regardless of whether higher or lower values are desirable.

## Yield Loss Contribution

```tableau
SUM([fail_quantity]) / { FIXED : SUM([production_quantity]) }
```

This is the selected mark's failed-unit contribution to total inspected production in the FIXED
filter context. It is not `1 - AVG([fpy])`.

## Defect Contribution %

```tableau
SUM([defect_quantity]) / { FIXED : SUM([defect_quantity]) }
```

Use on Defect Pareto and contributor views. Date/factory/product context filters define the
analysis cohort before the FIXED denominator is evaluated.

## Metric Status

Status is based on Favorable Variance: non-negative = **Favorable**. DPPM within 5,000 of its
benchmark and rates within 1 percentage point are **Watch**; larger unfavorable gaps are
**Unfavorable**. These thresholds classify the view and do not replace canonical metric
definitions.

## Existing governed calculations

The PR #12 calculations remain unchanged: weighted FPY, Defect Rate, DPPM, Rework Rate, Scrap
Rate, Product Mix Share, supplier-attributed Defect Rate, Defect Contribution, and cumulative
Pareto contribution. See `docs/metrics-definition.md` for their contracts.
