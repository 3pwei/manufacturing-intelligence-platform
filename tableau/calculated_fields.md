# Tableau Calculated Fields — MVP

Gold remains the source of truth. These fields aggregate governed additive columns at the current
Tableau filter grain. Create them in the named Tableau data source unless stated otherwise.

## Manufacturing Daily

### Production Quantity

```tableau
SUM([production_quantity])
```

### FPY

```tableau
IF SUM([pass_quantity]) + SUM([fail_quantity]) = 0 THEN NULL
ELSE SUM([pass_quantity]) /
     (SUM([pass_quantity]) + SUM([fail_quantity]))
END
```

### Defect Rate

```tableau
IF SUM([production_quantity]) = 0 THEN NULL
ELSE SUM([fail_quantity]) / SUM([production_quantity])
END
```

### DPPM

```tableau
IF SUM([production_quantity]) = 0 THEN NULL
ELSE SUM([fail_quantity]) * 1000000.0 / SUM([production_quantity])
END
```

### Rework Rate

```tableau
IF SUM([production_quantity]) = 0 THEN NULL
ELSE SUM([rework_quantity]) / SUM([production_quantity])
END
```

### Scrap Rate

```tableau
IF SUM([production_quantity]) = 0 THEN NULL
ELSE SUM([scrap_quantity]) / SUM([production_quantity])
END
```

### Yield Loss

```tableau
1 - [FPY]
```

### WoW FPY Change (percentage points)

Use the governed weekly value and display it only at a week-compatible view grain.

```tableau
AVG([wow_fpy_change])
```

Format as percentage with one or two decimals and label it **WoW FPY Change (pp)**. Do not sum the
daily repeated weekly value.

## Product Quality

### Product FPY

```tableau
IF SUM([pass_quantity]) + SUM([fail_quantity]) = 0 THEN NULL
ELSE SUM([pass_quantity]) /
     (SUM([pass_quantity]) + SUM([fail_quantity]))
END
```

### Product Mix Share

```tableau
IF WINDOW_SUM(SUM([production_quantity])) = 0 THEN NULL
ELSE SUM([production_quantity]) /
     WINDOW_SUM(SUM([production_quantity]))
END
```

Set **Compute Using** to Product within each displayed period/factory. The Gold
`product_mix_share` column is valid at its native daily factory-product grain, but the table
calculation above is required when dates are rolled up to month or an arbitrary filtered range.

## Supplier Quality

### Supplier-attributed Defect Rate

```tableau
IF SUM([inspected_units]) = 0 THEN NULL
ELSE SUM([defective_units]) / SUM([inspected_units])
END
```

Tooltip caveat: inspected units are completed units from distinct production lots with a
supplier-attributed event; the source has no BOM/allocation fact.

## Defect Pareto

### Defect Contribution

```tableau
IF WINDOW_SUM(SUM([defect_quantity])) = 0 THEN NULL
ELSE SUM([defect_quantity]) /
     WINDOW_SUM(SUM([defect_quantity]))
END
```

### Cumulative Defect Contribution

```tableau
RUNNING_SUM([Defect Contribution])
```

Sort Defect descending by `SUM([defect_quantity])` and compute along Defect.

## Formatting rules

- FPY, Defect Rate, Rework Rate, Scrap Rate, Mix Share: percentage.
- WoW FPY Change: percentage points, not percent change.
- DPPM and quantities: whole numbers with separators.
- Null denominators remain null; do not convert them to zero.
- Do not add FIXED / INCLUDE / EXCLUDE LOD expressions in PR #12. Those belong to PR #13.
