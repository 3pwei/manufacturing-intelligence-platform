# Data

- `generated/` is local, reproducible output and is excluded from version control.
- `sample/` is a seed-42, test-scale CSV fixture containing all five incident windows.
- `sample/ground_truth/incidents.json` is evaluation metadata, not an analytics input.

Regenerate the sample with:

```bash
python scripts/generate_data.py --seed 42 --scale test --format csv --output data/sample
```

All project data is synthetic or openly distributable.

Generated large datasets must not be committed to Git. PR #2 will add deterministic generation scripts and a small reviewable sample suitable for tests and demos.
