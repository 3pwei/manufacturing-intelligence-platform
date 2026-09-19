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
    assert len(actions.findall("nav-action")) >= 2
