"""Spark runtime for idempotent S3 Parquet to Bronze Delta ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .contracts import INGESTION_ORDER, TABLE_CONTRACTS, TableContract

METADATA_COLUMNS = ("_ingested_at", "_source_file", "_batch_id")


@dataclass(frozen=True)
class IngestionConfig:
    source_path: str
    catalog: str = "manufacturing_intelligence"
    bronze_schema: str = "bronze"
    quarantine_schema: str = "quarantine"
    batch_id: str = ""

    def resolved_batch_id(self) -> str:
        timestamp = datetime.now(timezone.utc)  # noqa: UP017 - Databricks uses Python 3.10.
        return self.batch_id or f"bronze-{timestamp:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"


class BronzeIngestion:
    """Run source-preserving ingestion. Spark is supplied by Databricks at runtime."""

    def __init__(self, spark: Any, config: IngestionConfig) -> None:
        self.spark = spark
        self.config = config
        self.batch_id = config.resolved_batch_id()
        from pyspark.sql import functions

        self.f = functions

    @property
    def bronze(self) -> str:
        return f"{self.config.catalog}.{self.config.bronze_schema}"

    @property
    def quarantine(self) -> str:
        return f"{self.config.catalog}.{self.config.quarantine_schema}"

    def setup(self) -> None:
        self.spark.sql(f"CREATE CATALOG IF NOT EXISTS {self.config.catalog}")
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.bronze}")
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.quarantine}")
        self.spark.sql(
            f"""CREATE TABLE IF NOT EXISTS {self.bronze}._ingestion_files (
              table_name STRING, source_file STRING, batch_id STRING, source_rows BIGINT,
              valid_rows BIGINT, quarantined_rows BIGINT, status STRING, processed_at TIMESTAMP
            ) USING DELTA"""
        )
        self.spark.sql(
            f"""CREATE TABLE IF NOT EXISTS {self.quarantine}.invalid_records (
              table_name STRING, original_record STRING, _source_file STRING, _batch_id STRING,
              _error_code STRING, _error_message STRING, _quarantined_at TIMESTAMP
            ) USING DELTA"""
        )

    def run(self) -> dict[str, dict[str, int]]:
        self.setup()
        return {name: self.ingest_table(TABLE_CONTRACTS[name]) for name in INGESTION_ORDER}

    def ingest_table(self, contract: TableContract) -> dict[str, int]:
        f = self.f
        source_glob = f"{self.config.source_path.rstrip('/')}/{contract.name}*.parquet"
        raw = self.spark.read.option("mergeSchema", "true").parquet(source_glob)
        raw = raw.withColumn("_source_file", f.col("_metadata.file_path"))
        processed = (
            self.spark.table(f"{self.bronze}._ingestion_files")
            .filter((f.col("table_name") == contract.name) & (f.col("status") == "SUCCESS"))
            .select("source_file")
            .distinct()
        )
        raw = raw.join(processed, raw._source_file == processed.source_file, "left_anti")
        if raw.limit(1).count() == 0:
            return {"source": 0, "valid": 0, "quarantined": 0, "skipped": 1}

        original_columns = raw.columns
        original_record = f.to_json(f.struct(*[f.col(name) for name in original_columns]))
        missing = {column.name for column in contract.columns} - set(original_columns)
        typed = raw
        for column in contract.columns:
            if column.name in original_columns:
                typed = typed.withColumn(
                    f"_raw_present_{column.name}", f.col(column.name).isNotNull()
                )
        for column in contract.columns:
            cast_expression = (
                f.expr(f"try_cast(`{column.name}` AS {column.data_type})")
                if column.name in original_columns
                else f.lit(None).cast(column.data_type)
            )
            typed = typed.withColumn(column.name, cast_expression)

        errors = []
        for column in contract.columns:
            if not column.nullable:
                code = (
                    "MISSING_REQUIRED_COLUMN" if column.name in missing else "NULL_REQUIRED_VALUE"
                )
                errors.append(
                    f.when(
                        f.col(column.name).isNull(),
                        f.struct(
                            f.lit(code).alias("code"),
                            f.lit(f"required field {column.name} is null or unavailable").alias(
                                "message"
                            ),
                        ),
                    )
                )
            if column.name in original_columns:
                errors.append(
                    f.when(
                        f.col(f"_raw_present_{column.name}") & typed[column.name].isNull(),
                        f.struct(
                            f.lit("INVALID_DATA_TYPE").alias("code"),
                            f.lit(f"{column.name} cannot be cast to {column.data_type}").alias(
                                "message"
                            ),
                        ),
                    )
                )
        for rule in contract.rules:
            errors.append(
                f.when(
                    ~f.coalesce(f.expr(rule.valid_when), f.lit(False)),
                    f.struct(f.lit(rule.code).alias("code"), f.lit(rule.message).alias("message")),
                )
            )

        typed = typed.withColumn("_original_record", original_record).withColumn(
            "_errors", f.array_compact(f.array(*errors))
        )
        typed = self._add_duplicate_errors(typed, contract)
        typed = self._add_foreign_key_errors(typed, contract)
        typed = typed.withColumn("_ingested_at", f.current_timestamp()).withColumn(
            "_batch_id", f.lit(self.batch_id)
        )

        invalid = typed.filter(f.size("_errors") > 0)
        valid = typed.filter(f.size("_errors") == 0)
        quarantine = invalid.select(
            f.lit(contract.name).alias("table_name"),
            f.col("_original_record").alias("original_record"),
            "_source_file",
            "_batch_id",
            f.concat_ws(",", f.transform("_errors", lambda x: x.code)).alias("_error_code"),
            f.concat_ws("; ", f.transform("_errors", lambda x: x.message)).alias("_error_message"),
            f.current_timestamp().alias("_quarantined_at"),
        )
        quarantine.write.mode("append").saveAsTable(f"{self.quarantine}.invalid_records")

        output_columns = [column.name for column in contract.columns] + list(METADATA_COLUMNS)
        valid.select(*output_columns).write.format("delta").mode("append").option(
            "mergeSchema", "false"
        ).saveAsTable(f"{self.bronze}.{contract.name}")
        source_count, valid_count, invalid_count = raw.count(), valid.count(), invalid.count()
        file_stats = (
            raw.groupBy("_source_file")
            .agg(f.count(f.lit(1)).alias("source_rows"))
            .join(
                valid.groupBy("_source_file").agg(f.count(f.lit(1)).alias("valid_rows")),
                "_source_file",
                "left",
            )
            .join(
                invalid.groupBy("_source_file").agg(f.count(f.lit(1)).alias("quarantined_rows")),
                "_source_file",
                "left",
            )
            .fillna(0, subset=["valid_rows", "quarantined_rows"])
        )
        audit = [
            (
                contract.name,
                row._source_file,
                self.batch_id,
                row.source_rows,
                row.valid_rows,
                row.quarantined_rows,
                "SUCCESS",
            )
            for row in file_stats.collect()
        ]
        audit_schema = "table_name string, source_file string, batch_id string, source_rows long, valid_rows long, quarantined_rows long, status string"
        self.spark.createDataFrame(audit, audit_schema).withColumn(
            "processed_at", f.current_timestamp()
        ).write.mode("append").saveAsTable(f"{self.bronze}._ingestion_files")
        return {
            "source": source_count,
            "valid": valid_count,
            "quarantined": invalid_count,
            "skipped": 0,
        }

    def _add_duplicate_errors(self, frame: Any, contract: TableContract) -> Any:
        from pyspark.sql.window import Window

        f = self.f
        duplicate = f.count(f.lit(1)).over(Window.partitionBy(*contract.key_columns)) > 1
        if self.spark.catalog.tableExists(f"{self.bronze}.{contract.name}"):
            aliases = [f"_existing_{offset}" for offset in range(len(contract.key_columns))]
            existing = (
                self.spark.table(f"{self.bronze}.{contract.name}")
                .select(
                    *[
                        f.col(name).alias(alias)
                        for name, alias in zip(contract.key_columns, aliases, strict=True)
                    ]
                )
                .distinct()
                .withColumn("_existing_key", f.lit(True))
            )
            join_on = [
                frame[name].eqNullSafe(existing[alias])
                for name, alias in zip(contract.key_columns, aliases, strict=True)
            ]
            frame = frame.join(existing, join_on, "left")
            duplicate = duplicate | f.col("_existing_key").isNotNull()
        else:
            aliases = []
        error = f.struct(
            f.lit("DUPLICATE_KEY").alias("code"),
            f.lit(f"duplicate key: {', '.join(contract.key_columns)}").alias("message"),
        )
        return frame.withColumn(
            "_errors",
            f.when(duplicate, f.array_union("_errors", f.array(error))).otherwise(f.col("_errors")),
        ).drop("_existing_key", *aliases)

    def _add_foreign_key_errors(self, frame: Any, contract: TableContract) -> Any:
        f = self.f
        result = frame
        for index, foreign_key in enumerate(contract.foreign_keys):
            aliases = [
                f"_parent_{index}_{offset}" for offset in range(len(foreign_key.parent_columns))
            ]
            parent = (
                self.spark.table(f"{self.bronze}.{foreign_key.parent_table}")
                .select(
                    *[
                        f.col(name).alias(alias)
                        for name, alias in zip(foreign_key.parent_columns, aliases, strict=True)
                    ]
                )
                .distinct()
            )
            marker = f"_fk_{index}"
            parent = parent.withColumn(marker, f.lit(True))
            condition = [
                result[child].eqNullSafe(parent[alias])
                for child, alias in zip(foreign_key.columns, aliases, strict=True)
            ]
            result = result.join(parent, condition, "left")
            nullable_value = f.lit(False)
            if foreign_key.nullable:
                for column in foreign_key.columns:
                    nullable_value = nullable_value | result[column].isNull()
            invalid = result[marker].isNull() & ~nullable_value
            error = f.struct(
                f.lit("INVALID_FOREIGN_KEY").alias("code"),
                f.lit(
                    f"{', '.join(foreign_key.columns)} does not resolve to {foreign_key.parent_table}"
                ).alias("message"),
            )
            result = result.withColumn(
                "_errors",
                f.when(invalid, f.array_union("_errors", f.array(error))).otherwise(
                    f.col("_errors")
                ),
            ).drop(marker, *aliases)
        return result
