from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pytest
from tableauhyperapi import Connection, CreateMode, HyperProcess, Telemetry

WORKBOOK = (
    Path(__file__).parents[1]
    / "tableau"
    / "manufacturing_intelligence_advanced_analytics.twbx"
)


def _extract_hyper(archive: ZipFile, directory: Path, marker: str) -> Path:
    member = next(
        name for name in archive.namelist() if name.endswith(".hyper") and marker in name
    )
    archive.extract(member, directory)
    return directory / member


def _table(connection: Connection) -> str:
    tables = connection.catalog.get_table_names("Extract")
    assert len(tables) == 1
    return str(tables[0])


def test_include_component_contributions_aggregate_to_one() -> None:
    with TemporaryDirectory() as temporary, ZipFile(WORKBOOK) as archive:
        hyper = _extract_hyper(archive, Path(temporary), "gold_defect_pareto")
        with (
            HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
            Connection(process.endpoint, hyper, CreateMode.NONE) as connection,
        ):
            table = _table(connection)
            total = connection.execute_scalar_query(
                f'SELECT SUM("defect_quantity") FROM {table}'
            )
            grouped = connection.execute_list_query(
                f'SELECT "component_id", SUM("defect_quantity") '
                f'FROM {table} GROUP BY "component_id"'
            )

    assert total > 0
    contributions = [quantity / total for _, quantity in grouped]
    assert contributions
    assert all(0 < contribution < 1 for contribution in contributions)
    assert sum(contributions) == pytest.approx(1.0)


def test_exclude_line_reference_matches_product_level_fpy() -> None:
    with TemporaryDirectory() as temporary, ZipFile(WORKBOOK) as archive:
        hyper = _extract_hyper(archive, Path(temporary), "gold_manufacturing_daily")
        with (
            HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
            Connection(process.endpoint, hyper, CreateMode.NONE) as connection,
        ):
            table = _table(connection)
            products = connection.execute_list_query(
                f'SELECT "product_id", SUM("pass_quantity"), '
                f'SUM("fail_quantity") FROM {table} GROUP BY "product_id"'
            )
            product_lines = connection.execute_list_query(
                f'SELECT "product_id", "line_id", SUM("pass_quantity"), '
                f'SUM("fail_quantity") FROM {table} '
                f'GROUP BY "product_id", "line_id"'
            )

    product_fpy = {
        product: passed / (passed + failed)
        for product, passed, failed in products
    }
    assert product_fpy
    for product, _line, _passed, _failed in product_lines:
        # EXCLUDE [line_id] retains Product in the selected/drilled scope, so
        # every line mark receives this same weighted Product reference.
        assert 0 < product_fpy[product] <= 1
