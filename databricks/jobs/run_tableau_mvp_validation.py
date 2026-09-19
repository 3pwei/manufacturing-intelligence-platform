"""Run machine-readable Tableau MVP acceptance checks in Databricks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    root = Path(parse_args().repository_root)
    sql_path = root / "sql/validation/040_tableau_mvp_validation.sql"
    if not sql_path.is_file():
        raise FileNotFoundError(f"required Tableau validation SQL not found: {sql_path}")

    statement = sql_path.read_text()
    rows = [row.asDict(recursive=True) for row in spark.sql(statement).collect()]  # noqa: F821
    for row in rows:
        print(json.dumps({"event": "tableau_mvp_validation", **row}, ensure_ascii=False))

    failures = [row for row in rows if row["status"] != "PASS"]
    summary = {
        "event": "tableau_mvp_validation_completed",
        "status": "FAIL" if failures else "PASS",
        "checks": len(rows),
        "failures": len(failures),
        "failed_checks": [row["check_name"] for row in failures],
    }
    print(json.dumps(summary, ensure_ascii=False))
    if failures:
        raise RuntimeError(
            "Tableau MVP acceptance failed: "
            + ", ".join(row["check_name"] for row in failures)
        )
