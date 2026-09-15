# Tableau Calculated Fields Plan

Canonical KPI arithmetic should come from governed numerators/denominators where possible. Tableau calculations focus on interactive analysis and presentation grain.

Planned fields include:

## FPY

```tableau
SUM([First Pass Pass Qty]) /
(SUM([First Pass Pass Qty]) + SUM([Fail Qty]))
```

## Yield Loss

```tableau
1 - [FPY]
```

## FPY Status

Conceptual status using a parameterized target/tolerance:

```tableau
IF [FPY] >= [FPY Target] THEN "On Target"
ELSEIF [FPY] >= [FPY Target] - [Warning Tolerance] THEN "Watch"
ELSE "Action Required"
END
```

## Period labels and deltas

Week-over-week percentage-point deltas, selected-period vs baseline labels, and contribution formatting may use table calculations when view-order semantics are intentional.

## Rule

If a calculation defines business truth used across tools, move it upstream to the governed SQL/Gold layer and document it in `docs/metrics-definition.md`.
