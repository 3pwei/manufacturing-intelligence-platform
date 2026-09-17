from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
VALIDATION_SQL = (ROOT / "sql/validation/040_tableau_mvp_validation.sql").read_text()
VALIDATION_JOB = ROOT / "databricks/jobs/tableau_mvp_validation_job.yml"
VALIDATION_RUNNER = ROOT / "databricks/jobs/run_tableau_mvp_validation.py"


def test_tableau_acceptance_covers_gold_metrics_and_incidents() -> None:
    required_checks = {
        "gold_table_inventory",
        "governed_metric_formulas",
        "incident_a_supplier_power_module",
        "incident_b_mexico_line2_voltage",
        "incident_c_ramp_line_improves",
        "incident_d_localized_memory_failure",
        "incident_e_aggregate_fpy_declines",
        "incident_e_product_fpy_stable",
        "incident_e_product_mix_shift",
    }
    assert all(check in VALIDATION_SQL for check in required_checks)
    assert VALIDATION_SQL.count("row_count_") == 1
    assert "status" in VALIDATION_SQL
    assert "'PASS'" in VALIDATION_SQL
    assert "'FAIL'" in VALIDATION_SQL


def test_tableau_acceptance_reads_only_gold_business_tables() -> None:
    lower = VALIDATION_SQL.lower()
    assert "manufacturing_intelligence.bronze" not in lower
    assert "manufacturing_intelligence.silver" not in lower
    for table in (
        "gold_manufacturing_daily",
        "gold_factory_quality",
        "gold_product_quality",
        "gold_supplier_quality",
        "gold_defect_pareto",
    ):
        assert f"manufacturing_intelligence.gold.{table}" in lower


def test_tableau_validation_job_is_serverless_and_fail_closed() -> None:
    resource = yaml.safe_load(VALIDATION_JOB.read_text())
    job = resource["resources"]["jobs"]["tableau_mvp_validation"]
    task = job["tasks"][0]
    assert task["environment_key"] == "serverless"
    assert task["spark_python_task"]["python_file"].endswith("run_tableau_mvp_validation.py")
    runner = VALIDATION_RUNNER.read_text()
    assert "if failures:" in runner
    assert "raise RuntimeError" in runner
