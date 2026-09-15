# Business Requirements

## Personas

### Manufacturing Operations Manager
Needs a fast view of yield health, line performance, trend changes, and the operational area requiring attention.

### Quality Manager
Needs defect Pareto, failure concentration, rework/scrap trends, component attribution, and evidence for corrective action.

### Supplier Quality Analyst
Needs to understand whether defects correlate with supplier/component/lot combinations and how much they contribute to loss.

### Business / Data Analyst
Needs trusted metrics, flexible segmentation, drill-down, repeatable SQL, and documented metric definitions.

### Engineering Manager
Needs evidence linking operational symptoms to process, test, component, and product conditions.

## Primary MVP scenario

A weekly FPY decline is observed. The analyst must determine:

- which factory contributed most;
- whether the issue is product- or mix-driven;
- which line, component, supplier, and defect types are concentrated;
- the percentage-point and relative contribution to yield loss;
- whether the root cause is supplier quality, test-station behavior, line ramp-up, component lot quality, or aggregation bias;
- what should be investigated next.

## Core business questions

1. What is current FPY and how did it change week over week?
2. Which factory/product/line contributed most to the change?
3. Which defects dominate failures and yield loss?
4. Are defects concentrated by component, supplier, or lot?
5. How does a selected entity compare with its factory/product benchmark?
6. Is an aggregate decline explained by mix shift rather than within-segment deterioration?
7. What evidence supports the proposed root cause?

## MVP acceptance story

A five-minute demo should move from executive KPI → anomalous period → dimensional drill-down → root-cause evidence → recommended business investigation without changing tools or inventing unsupported conclusions.
