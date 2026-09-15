from manufacturing_analytics.bronze.contracts import INGESTION_ORDER, TABLE_CONTRACTS
from manufacturing_analytics.bronze.ingestion import METADATA_COLUMNS, IngestionConfig


def test_all_source_tables_have_contracts() -> None:
    assert INGESTION_ORDER == (
        "dim_date",
        "dim_factory",
        "dim_line",
        "dim_product",
        "dim_component",
        "dim_supplier",
        "dim_defect",
        "fact_production",
        "fact_quality_event",
    )
    assert set(INGESTION_ORDER) == set(TABLE_CONTRACTS)


def test_contract_keys_and_columns_are_consistent() -> None:
    for contract in TABLE_CONTRACTS.values():
        columns = {column.name for column in contract.columns}
        assert contract.key_columns
        assert set(contract.key_columns) <= columns
        assert len(columns) == len(contract.columns)
        assert all(set(foreign_key.columns) <= columns for foreign_key in contract.foreign_keys)


def test_required_quality_rules_are_declared() -> None:
    codes = {rule.code for contract in TABLE_CONTRACTS.values() for rule in contract.rules}
    assert {
        "DATE_OUT_OF_RANGE",
        "NEGATIVE_QUANTITY",
        "INVALID_PRODUCTION_TOTAL",
        "INVALID_EVENT_QUANTITY",
    } <= codes
    assert any(
        fk.parent_table == "fact_production"
        for fk in TABLE_CONTRACTS["fact_quality_event"].foreign_keys
    )


def test_metadata_and_safe_defaults() -> None:
    assert METADATA_COLUMNS == ("_ingested_at", "_source_file", "_batch_id")
    config = IngestionConfig("s3://manufacturing-intelligence-3pwei/source/synthetic/")
    assert config.catalog == "manufacturing_intelligence"
    assert len(config.resolved_batch_id()) > 20
