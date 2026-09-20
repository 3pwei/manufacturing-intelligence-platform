import xml.etree.ElementTree as etree
from pathlib import Path
from zipfile import ZipFile

WORKBOOK = Path(__file__).parents[1] / "tableau" / "manufacturing_intelligence_advanced_analytics.twbx"


def _tree() -> etree.ElementTree:
    with ZipFile(WORKBOOK) as archive:
        twb = next(name for name in archive.namelist() if name.endswith(".twb"))
        return etree.ElementTree(etree.fromstring(archive.read(twb)))


def test_package_is_sanitized_and_extract_only() -> None:
    with ZipFile(WORKBOOK) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert sum(name.endswith(".hyper") for name in names) == 2
        content = b"\n".join(archive.read(name) for name in names if name.endswith(".twb")).lower()
    for marker in (b"dbc-", b"databricks", b"v-http-path", b"warehouse", b"username=", b"password=", b"token="):
        assert marker not in content


def test_parameters_lods_calculations_and_actions_exist() -> None:
    tree = _tree()
    parameters = tree.find("./datasources/datasource[@name='Parameters']")
    assert parameters is not None
    assert len(parameters.findall("column")) == 2
    formulas = "\n".join(node.get("formula", "") for node in tree.iter("calculation"))
    for token in ("{ FIXED", "{ INCLUDE", "{ EXCLUDE"):
        assert token in formulas
    captions = {node.get("caption") for node in tree.iter("column")}
    assert {"Selected Metric", "Variance vs Benchmark", "Yield Loss Contribution", "Defect Contribution %", "Metric Status"} <= captions
    actions = tree.find("actions")
    assert actions is not None
    commands = [node.get("command") for node in actions.iter("command")]
    assert commands.count("tsc:tsl-filter") >= 2
    assert commands.count("tsc:brush") >= 1
    assert not actions.findall("nav-action")


def test_calculated_columns_precede_column_instances() -> None:
    tree = _tree()
    for datasource in tree.findall("./datasources/datasource"):
        children = list(datasource)
        instance_indexes = [
            index for index, child in enumerate(children) if child.tag == "column-instance"
        ]
        if not instance_indexes:
            continue
        first_instance = min(instance_indexes)
        calculation_indexes = [
            index
            for index, child in enumerate(children)
            if child.tag == "column" and child.get("name", "").startswith("[Calculation_PR13_")
        ]
        assert calculation_indexes
        assert max(calculation_indexes) < first_instance


def test_parameter_driven_calculations_are_wired_to_worksheets() -> None:
    tree = _tree()
    metric_instance = "[usr:Calculation_PR13_Selected_Metric:qk]"
    benchmark_instance = "[usr:Calculation_PR13_Selected_Benchmark:qk]"
    analysis_instance = "[usr:Calculation_PR13_Analysis_Value:qk]"
    active_instances = {
        "Selected Metric Trend": metric_instance,
        "Metric vs Benchmark Trend": analysis_instance,
        "Quality - Factory Comparison": analysis_instance,
        "Quality - Product Comparison": analysis_instance,
    }
    for name, active_instance in active_instances.items():
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        xml = etree.tostring(worksheet, encoding="unicode")
        assert metric_instance in xml
        table = worksheet.find("table")
        assert table is not None
        active_view_xml = "".join(
            etree.tostring(node, encoding="unicode")
            for node in (table.find("rows"), table.find("cols"), table.find("panes"))
            if node is not None
        )
        assert active_instance in active_view_xml
        assert "[usr:Calculation_0659753060524032:qk]" not in active_view_xml
        parameter_dependency = worksheet.find(
            ".//datasource-dependencies[@datasource='Parameters']"
        )
        assert parameter_dependency is not None
    for name in ("Quality - Factory Comparison", "Quality - Product Comparison"):
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        assert benchmark_instance in etree.tostring(worksheet, encoding="unicode")


def test_parameter_driven_kpi_cards_are_visible() -> None:
    tree = _tree()
    expectations = {
        "KPI - FPY": (
            "[usr:Calculation_PR13_Selected_Metric:qk]",
            "Selected Metric",
        ),
        "KPI - WoW FPY Change": (
            "[usr:Calculation_PR13_Variance:qk]",
            "Variance vs Benchmark",
        ),
    }
    for name, (instance, label) in expectations.items():
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        xml = etree.tostring(worksheet, encoding="unicode")
        assert instance in xml
        assert label in xml
        assert worksheet.find(
            ".//datasource-dependencies[@datasource='Parameters']"
        ) is not None


def test_lods_are_used_by_visible_business_views() -> None:
    tree = _tree()
    active_fields = {
        "RCA - Component Contribution": "[usr:Calculation_PR13_Include_Component:qk]",
        "RCA - Supplier Contribution": "[usr:Calculation_PR13_Defect_Contribution:qk]",
        "RCA - Defect Pareto": "[usr:Calculation_PR13_Defect_Contribution:qk]",
        "Quality - Line Comparison": "[usr:Calculation_PR13_Exclude_Line:qk]",
    }
    for name, field in active_fields.items():
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        table = worksheet.find("table")
        assert table is not None
        active_xml = "".join(
            etree.tostring(node, encoding="unicode")
            for node in (table.find("rows"), table.find("cols"), table.find("panes"))
            if node is not None
        )
        assert field in active_xml

    quality = tree.find("./dashboards/dashboard[@name='Manufacturing Quality']")
    assert quality is not None
    assert quality.find(".//zone[@name='Quality - Line Comparison']") is not None

    actions = tree.find("actions")
    assert actions is not None
    captions = {action.get("caption") for action in actions.findall("action")}
    assert "Filter defect contributors from Pareto" in captions
    assert "Highlight related defect contributors" in captions


def test_dashboard_zones_precede_zone_styles() -> None:
    tree = _tree()
    for parent in tree.iter():
        children = list(parent)
        zone_indexes = [index for index, child in enumerate(children) if child.tag == "zone"]
        style_indexes = [
            index for index, child in enumerate(children) if child.tag == "zone-style"
        ]
        if zone_indexes and style_indexes:
            assert max(zone_indexes) < min(style_indexes)
