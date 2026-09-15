# Tableau LOD Expression Plan

LOD expressions must answer real view-grain questions rather than exist only to demonstrate syntax.

## FIXED — Factory FPY Benchmark

**Question:** While drilling into product, line, component, or defect, what is the selected factory's overall FPY benchmark?

Conceptual calculation:

```tableau
{ FIXED [Factory ID] : SUM([First Pass Pass Qty]) }
/
{ FIXED [Factory ID] : SUM([First Pass Pass Qty]) + SUM([Fail Qty]) }
```

Filter-order behavior must be tested and documented during workbook implementation.

## FIXED — Product Benchmark

**Question:** How does the selected line compare with the product's overall performance independent of line-level detail?

## INCLUDE — Component Contribution Context

**Question:** When presenting a higher-level product view, can component-level failures be incorporated to compute contribution without permanently exposing component as a view dimension?

## EXCLUDE — Higher-level trend

**Question:** When a detailed mark includes component or defect, what does the parent product/factory trend look like without that lower-level dimension?

## Validation

Every implemented LOD must be cross-checked against an equivalent governed SQL result for controlled test slices.
