CREATE CATALOG IF NOT EXISTS manufacturing_intelligence;
CREATE SCHEMA IF NOT EXISTS manufacturing_intelligence.bronze;
CREATE SCHEMA IF NOT EXISTS manufacturing_intelligence.quarantine;

CREATE TABLE IF NOT EXISTS manufacturing_intelligence.bronze._ingestion_files (
  table_name STRING,
  source_file STRING,
  batch_id STRING,
  source_rows BIGINT,
  valid_rows BIGINT,
  quarantined_rows BIGINT,
  status STRING,
  processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS manufacturing_intelligence.quarantine.invalid_records (
  table_name STRING,
  original_record STRING,
  _source_file STRING,
  _batch_id STRING,
  _error_code STRING,
  _error_message STRING,
  _quarantined_at TIMESTAMP
) USING DELTA;
