# AI Analytics Boundary

## Principle

The AI layer is an analyst assistant, not the source of metric truth.

```text
User Question
→ Intent / metric selection
→ Governed metric or approved analytical query
→ Structured result + comparison baseline
→ Evidence package
→ Explanation
→ Recommended next analytical step
```

## AI may

- translate a business question into approved analytical intents;
- choose relevant governed metrics/dimensions;
- compare periods and segments;
- rank contributors using returned evidence;
- summarize findings in business language;
- suggest follow-up analysis or operational checks.

## AI must not

- invent values missing from query results;
- redefine KPI formulas;
- claim causation from correlation without supporting evidence;
- bypass row/column governance in a future multi-user implementation;
- execute unrestricted arbitrary SQL against production data.

## Evidence contract

A future AI response should be able to state or attach:
- metric name;
- reporting period;
- comparison baseline;
- dimensions/filters;
- major contributors;
- query/model identifier;
- uncertainty or caveats.

This enables the demo to distinguish trustworthy analytics assistance from generic chatbot output.
