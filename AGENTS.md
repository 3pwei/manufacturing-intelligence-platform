# AGENTS.md

## Project objective

Build a portfolio-grade manufacturing analytics platform that demonstrates business requirement translation, manufacturing analytics, data modeling, advanced SQL, Python, Databricks, Tableau, data governance, and AI-assisted analysis.

## Architecture principles

- Keep data generation, ingestion, transformations, business metrics, visualization, and AI orchestration separated.
- Gold-layer metrics and governed SQL views are the business truth.
- Do not independently redefine the same KPI in Python, SQL, Tableau, and AI prompts.
- AI may interpret evidence; it must not invent metric values or bypass governed data.
- Synthetic data must be deterministic when a random seed is supplied.
- Prefer simple, reviewable architecture over unnecessary services.

## Data modeling conventions

- Every fact table must document its grain before implementation.
- Dimension keys must be explicit and stable.
- Natural-key uniqueness and referential integrity must be testable.
- Metric numerator, denominator, filters, grain, and caveats are contracts.
- Changes to a business metric require updating `docs/metrics-definition.md`.

## Python conventions

- Python 3.12+.
- Use type hints for public functions.
- Prefer `pathlib` over string-based filesystem manipulation.
- Separate domain logic from I/O and infrastructure.
- Prefer deterministic pure functions where practical.
- Avoid large frameworks unless a concrete requirement justifies them.

## SQL conventions

- Use readable CTEs and descriptive aliases.
- Avoid `SELECT *` in governed analytical models.
- Make grain-changing aggregations explicit.
- Document window-function and benchmark logic when non-obvious.
- Keep reusable business logic in governed models/views rather than copying it into dashboard queries.

## Tableau conventions

- Use LOD Expressions only for a real business-grain requirement.
- Document all important Calculated Fields and LODs under `tableau/`.
- Dashboard filters, parameters, actions, and drill paths must map to business questions.
- Avoid embedding canonical KPI definitions only inside a workbook.

## AI analytics boundary

The intended path is:

User Question → Analytics Agent → Governed Metric / SQL Layer → Query Result → Evidence → Explanation

AI is responsible for interpretation, investigation orchestration, explanation, and suggested analytical next steps. It is not the metric source of truth.

## Testing expectations

- Unit-test reusable domain logic.
- Add data-quality tests for schema, ranges, uniqueness, and referential integrity.
- Add regression tests for synthetic incident outcomes.
- A PR that changes a metric must include or update metric tests.

## Documentation expectations

Keep these documents current:
- `docs/architecture.md`
- `docs/business-requirements.md`
- `docs/data-model.md`
- `docs/data-dictionary.md`
- `docs/metrics-definition.md`
- `docs/incidents.md`

## PR scope discipline

- Prefer small, reviewable PRs.
- Do not rewrite architecture without a clear documented reason.
- Do not combine unrelated refactors with feature work.
- State business impact, data-model impact, and validation results in every substantial PR.
- Do not commit credentials, tokens, proprietary data, or company-confidential information.
