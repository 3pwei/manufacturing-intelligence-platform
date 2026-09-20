from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_public_validation_covers_all_dashboards_and_parameter_scenarios() -> None:
    script = (ROOT / "scripts" / "validate_tableau_public.py").read_text(encoding="utf-8")
    for dashboard in (
        "Executive Overview",
        "Manufacturing Quality",
        "Root Cause Analysis",
    ):
        assert dashboard in script
    assert '"Metric Selector": "FPY"' in script
    assert '"Metric Selector": "DPPM"' in script
    assert '"Benchmark Selector": "Overall"' in script
    assert '"Benchmark Selector": "Product"' in script
    assert "parameter_scenarios_differ" in script
    assert "ERROR_MARKERS" in script


def test_public_validation_workflow_preserves_screenshot_evidence() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "tableau-public-validation.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "scripts/validate_tableau_public.py" in workflow
    assert "if: always()" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "artifacts/tableau-public" in workflow
