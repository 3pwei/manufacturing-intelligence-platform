# Tableau Calculated Fields — Advanced Analytics

Gold remains the metric source of truth. Tableau calculations change presentation grain and
interaction only; rates are always recomputed from additive numerators and denominators.

## Parameters

### Metric Selector

String list: `FPY`, `Defect Rate`, `DPPM`, `Rework Rate`, `Scrap Rate`. Default: `FPY`.

### Benchmark Selector

String list: `Overall`, `Factory`, `Product`. Default: `Factory`.

The benchmark selector applies to FPY comparison. Other selected metrics remain visible but return
null for `Variance vs Benchmark`, preventing unlike units from being compared.

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

## Selected FPY Benchmark

```tableau
CASE [Benchmark Selector]
WHEN "Overall" THEN [Overall FPY Benchmark (FIXED)]
WHEN "Factory" THEN [Factory FPY Benchmark (FIXED)]
WHEN "Product" THEN [Product FPY Benchmark (FIXED)]
END
```

## Variance vs Benchmark

```tableau
IF [Metric Selector] = "FPY" THEN
  [Selected Metric] - [Selected FPY Benchmark]
END
```

Display as percentage points. A negative value means the selected mark is below the chosen FPY
reference.

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

For FPY, status is based on variance to the selected benchmark: non-negative = **On / Above
Benchmark**, within -1 percentage point = **Watch**, otherwise **Action Required**. DPPM uses
30,000/50,000 display thresholds; the other rates use 3%/5%. These thresholds classify the view;
they do not replace canonical metric definitions.

## Existing governed calculations

The PR #12 calculations remain unchanged: weighted FPY, Defect Rate, DPPM, Rework Rate, Scrap
Rate, Product Mix Share, supplier-attributed Defect Rate, Defect Contribution, and cumulative
Pareto contribution. See `docs/metrics-definition.md` for their contracts.

