-- PR #11 deployment verification. All *_violations queries must return zero.

SELECT table_schema, table_name
FROM manufacturing_intelligence.information_schema.tables
WHERE table_schema IN ('bronze', 'quarantine', 'silver', 'gold')
ORDER BY table_schema, table_name;

-- Bronze counts must match the uploaded seed-42 demo inventory.
SELECT 'dim_date' AS table_name, COUNT(*) AS actual_rows, 181 AS expected_rows
FROM manufacturing_intelligence.bronze.dim_date
UNION ALL SELECT 'dim_factory', COUNT(*), 3 FROM manufacturing_intelligence.bronze.dim_factory
UNION ALL SELECT 'dim_line', COUNT(*), 6 FROM manufacturing_intelligence.bronze.dim_line
UNION ALL SELECT 'dim_product', COUNT(*), 5 FROM manufacturing_intelligence.bronze.dim_product
UNION ALL SELECT 'dim_component', COUNT(*), 6 FROM manufacturing_intelligence.bronze.dim_component
UNION ALL SELECT 'dim_supplier', COUNT(*), 8 FROM manufacturing_intelligence.bronze.dim_supplier
UNION ALL SELECT 'dim_defect', COUNT(*), 6 FROM manufacturing_intelligence.bronze.dim_defect
UNION ALL SELECT 'fact_production', COUNT(*), 2110
FROM manufacturing_intelligence.bronze.fact_production
UNION ALL SELECT 'fact_quality_event', COUNT(*), 9488
FROM manufacturing_intelligence.bronze.fact_quality_event
ORDER BY table_name;

SELECT table_name, _error_code, COUNT(*) AS records
FROM manufacturing_intelligence.quarantine.invalid_records
GROUP BY table_name, _error_code ORDER BY table_name, records DESC;

SELECT table_name, source_file, status,
       SUM(source_rows) AS source_rows, SUM(valid_rows) AS valid_rows,
       SUM(quarantined_rows) AS quarantined_rows, COUNT(*) AS successful_audit_records
FROM manufacturing_intelligence.bronze._ingestion_files
GROUP BY table_name, source_file, status ORDER BY table_name, source_file;

-- Rerunning unchanged files must leave exactly one successful audit row per source URI.
SELECT 'duplicate_successful_source_audit' AS check_name, COUNT(*) AS violations
FROM (
  SELECT table_name, source_file
  FROM manufacturing_intelligence.bronze._ingestion_files
  WHERE status = 'SUCCESS'
  GROUP BY table_name, source_file HAVING COUNT(*) > 1
);

SELECT 'silver_fact_production_duplicate' AS check_name, COUNT(*) AS violations
FROM (SELECT production_date, factory_id, line_id, product_id, production_lot_id
      FROM manufacturing_intelligence.silver.silver_fact_production
      GROUP BY ALL HAVING COUNT(*) > 1);

SELECT 'silver_quality_event_duplicate' AS check_name, COUNT(*) AS violations
FROM (SELECT quality_event_id
      FROM manufacturing_intelligence.silver.silver_fact_quality_event
      GROUP BY quality_event_id HAVING COUNT(*) > 1);

SELECT 'invalid_production_quantities' AS check_name, COUNT(*) AS violations
FROM manufacturing_intelligence.silver.silver_fact_production
WHERE completed_qty < 0 OR first_pass_pass_qty < 0 OR fail_qty < 0
   OR first_pass_pass_qty + fail_qty > started_qty
   OR rework_qty > fail_qty OR scrap_qty > fail_qty;

SELECT 'gold_manufacturing_daily' AS table_name, COUNT(*) AS actual_rows, 1798 AS expected_rows
FROM manufacturing_intelligence.gold.gold_manufacturing_daily
UNION ALL SELECT 'gold_factory_quality', COUNT(*), 543
FROM manufacturing_intelligence.gold.gold_factory_quality
UNION ALL SELECT 'gold_product_quality', COUNT(*), 1442
FROM manufacturing_intelligence.gold.gold_product_quality
UNION ALL SELECT 'gold_supplier_quality', COUNT(*), 8045
FROM manufacturing_intelligence.gold.gold_supplier_quality
UNION ALL SELECT 'gold_defect_pareto', COUNT(*), 8649
FROM manufacturing_intelligence.gold.gold_defect_pareto
ORDER BY table_name;

-- Incident A-D evidence remains discoverable without reading the ground-truth manifest.
SELECT 'INC-A' AS incident_id, supplier_id, component_id,
       SUM(defective_units) AS defective_units,
       SUM(defective_units) / NULLIF(SUM(inspected_units), 0) AS defect_rate
FROM manufacturing_intelligence.gold.gold_supplier_quality
WHERE event_date BETWEEN DATE '2026-03-15' AND DATE '2026-04-12'
GROUP BY supplier_id, component_id ORDER BY defective_units DESC;

SELECT 'INC-B' AS incident_id, factory_id, line_id, defect_id,
       SUM(defect_quantity) AS defect_quantity
FROM manufacturing_intelligence.gold.gold_defect_pareto
WHERE event_date BETWEEN DATE '2026-04-15' AND DATE '2026-05-05'
GROUP BY factory_id, line_id, defect_id ORDER BY defect_quantity DESC;

SELECT 'INC-C' AS incident_id, production_date, factory_id, line_id,
       SUM(rework_quantity) / NULLIF(SUM(production_quantity), 0) AS rework_rate,
       SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS fpy
FROM manufacturing_intelligence.gold.gold_manufacturing_daily
WHERE factory_id = 'FAC-MY' AND production_date BETWEEN DATE '2026-02-01' AND DATE '2026-05-31'
GROUP BY production_date, factory_id, line_id ORDER BY production_date, line_id;

SELECT 'INC-D' AS incident_id, component_lot_id, supplier_id, component_id,
       SUM(event_quantity) AS event_quantity
FROM manufacturing_intelligence.silver.silver_fact_quality_event
WHERE event_date BETWEEN DATE '2026-05-10' AND DATE '2026-05-16'
GROUP BY component_lot_id, supplier_id, component_id ORDER BY event_quantity DESC;

-- Incident E acceptance: aggregate Mexico FPY falls after the mix shift while product FPY
-- remains approximately stable.
WITH aggregate_period AS (
  SELECT CASE WHEN production_date < DATE '2026-06-01' THEN 'pre' ELSE 'post' END AS period,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS aggregate_fpy
  FROM manufacturing_intelligence.gold.gold_factory_quality
  WHERE factory_id = 'FAC-MX'
    AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
  GROUP BY period
), product_period AS (
  SELECT product_id,
         CASE WHEN production_date < DATE '2026-06-01' THEN 'pre' ELSE 'post' END AS period,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS product_fpy
  FROM manufacturing_intelligence.gold.gold_product_quality
  WHERE factory_id = 'FAC-MX'
    AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
  GROUP BY product_id, period
), product_change AS (
  SELECT pre.product_id, post.product_fpy - pre.product_fpy AS fpy_change
  FROM product_period pre JOIN product_period post ON pre.product_id = post.product_id
  WHERE pre.period = 'pre' AND post.period = 'post'
)
SELECT
  MAX(CASE WHEN period = 'pre' THEN aggregate_fpy END) AS aggregate_pre_fpy,
  MAX(CASE WHEN period = 'post' THEN aggregate_fpy END) AS aggregate_post_fpy,
  MAX(CASE WHEN period = 'post' THEN aggregate_fpy END)
    - MAX(CASE WHEN period = 'pre' THEN aggregate_fpy END) AS aggregate_fpy_change,
  (SELECT AVG(ABS(fpy_change)) FROM product_change) AS mean_absolute_product_fpy_change
FROM aggregate_period;

SELECT production_date, factory_id, product_id, production_quantity, fpy, product_mix_share
FROM manufacturing_intelligence.gold.gold_product_quality
WHERE factory_id = 'FAC-MX' AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
ORDER BY production_date, product_id;
