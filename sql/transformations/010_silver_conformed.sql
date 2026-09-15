-- Silver preserves the PR #1 fact grains. CREATE OR REPLACE makes a full refresh idempotent.
CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_date USING DELTA AS
SELECT date_id, date, year, quarter, month, week_of_year, day_of_week, is_weekend,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY date_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_date) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_factory USING DELTA AS
SELECT trim(factory_id) AS factory_id, upper(trim(factory_code)) AS factory_code,
       trim(factory_name) AS factory_name, trim(country) AS country, baseline_fpy,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY factory_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_factory) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_line USING DELTA AS
SELECT trim(l.line_id) AS line_id, upper(trim(l.line_code)) AS line_code,
       trim(l.line_name) AS line_name, trim(l.factory_id) AS factory_id, l.is_ramp_line,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY line_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_line) l
JOIN manufacturing_intelligence.silver.silver_dim_factory f ON l.factory_id = f.factory_id
WHERE l._rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_product USING DELTA AS
SELECT trim(product_id) AS product_id, upper(trim(product_code)) AS product_code,
       trim(product_name) AS product_name, trim(product_family) AS product_family,
       complexity_risk, current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY product_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_product) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_component USING DELTA AS
SELECT trim(component_id) AS component_id, upper(trim(component_code)) AS component_code,
       trim(component_name) AS component_name, trim(component_family) AS component_family,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY component_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_component) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_supplier USING DELTA AS
SELECT trim(supplier_id) AS supplier_id, upper(trim(supplier_code)) AS supplier_code,
       trim(supplier_name) AS supplier_name, trim(supplier_region) AS supplier_region,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY supplier_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_supplier) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_dim_defect USING DELTA AS
SELECT trim(defect_id) AS defect_id, upper(trim(defect_code)) AS defect_code,
       trim(defect_name) AS defect_name, trim(defect_category) AS defect_category,
       lower(trim(severity)) AS severity, current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY defect_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.dim_defect) WHERE _rn = 1;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_fact_production USING DELTA AS
SELECT p.production_lot_id, p.production_date, p.factory_id, p.line_id, p.product_id,
       p.production_qty, p.pass_qty, p.started_qty, p.completed_qty,
       p.first_pass_pass_qty, p.fail_qty, p.rework_qty, p.scrap_qty,
       year(p.production_date) AS production_year, weekofyear(p.production_date) AS production_week,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (
        PARTITION BY production_date, factory_id, line_id, product_id, production_lot_id
        ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.fact_production) p
JOIN manufacturing_intelligence.silver.silver_dim_date d ON p.production_date = d.date
JOIN manufacturing_intelligence.silver.silver_dim_factory f ON p.factory_id = f.factory_id
JOIN manufacturing_intelligence.silver.silver_dim_line l
  ON p.line_id = l.line_id AND p.factory_id = l.factory_id
JOIN manufacturing_intelligence.silver.silver_dim_product pr ON p.product_id = pr.product_id
WHERE p._rn = 1 AND p.production_qty >= 0 AND p.pass_qty >= 0 AND p.started_qty >= 0
  AND p.completed_qty >= 0 AND p.first_pass_pass_qty >= 0 AND p.fail_qty >= 0
  AND p.rework_qty >= 0 AND p.scrap_qty >= 0
  AND p.pass_qty + p.fail_qty = p.production_qty
  AND p.completed_qty <= p.started_qty
  AND p.first_pass_pass_qty + p.fail_qty <= p.started_qty
  AND p.rework_qty <= p.fail_qty AND p.scrap_qty <= p.fail_qty;

CREATE OR REPLACE TABLE manufacturing_intelligence.silver.silver_fact_quality_event USING DELTA AS
SELECT q.quality_event_id, q.event_date, q.event_timestamp, q.production_lot_id,
       q.factory_id, q.line_id, q.product_id, q.component_id, q.supplier_id,
       q.component_lot_id, q.defect_id, lower(trim(q.inspection_stage)) AS inspection_stage,
       q.event_quantity, q.is_first_pass_failure, q.is_rework, q.is_scrap,
       lower(trim(q.disposition)) AS disposition,
       q.supplier_id IS NOT NULL AS is_supplier_attributed,
       current_timestamp() AS _silver_updated_at
FROM (SELECT *, row_number() OVER (PARTITION BY quality_event_id ORDER BY _ingested_at DESC) AS _rn
      FROM manufacturing_intelligence.bronze.fact_quality_event) q
JOIN manufacturing_intelligence.silver.silver_fact_production p
  ON q.production_lot_id = p.production_lot_id AND q.event_date = p.production_date
 AND q.factory_id = p.factory_id AND q.line_id = p.line_id AND q.product_id = p.product_id
JOIN manufacturing_intelligence.silver.silver_dim_component c ON q.component_id = c.component_id
JOIN manufacturing_intelligence.silver.silver_dim_defect d ON q.defect_id = d.defect_id
LEFT JOIN manufacturing_intelligence.silver.silver_dim_supplier s ON q.supplier_id = s.supplier_id
WHERE q._rn = 1 AND q.event_quantity > 0
  AND q.inspection_stage IN ('incoming', 'in_process', 'final', 'test')
  AND q.disposition IN ('fail', 'rework', 'scrap')
  AND (q.supplier_id IS NULL OR s.supplier_id IS NOT NULL);

