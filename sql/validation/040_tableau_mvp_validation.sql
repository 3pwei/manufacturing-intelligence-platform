-- PR #12 machine-readable Tableau MVP acceptance.
-- The Databricks job fails when any row returns FAIL.
WITH
required_tables AS (
  SELECT COUNT(*) AS actual
  FROM manufacturing_intelligence.information_schema.tables
  WHERE table_schema = 'gold'
    AND table_name IN (
      'gold_manufacturing_daily',
      'gold_factory_quality',
      'gold_product_quality',
      'gold_supplier_quality',
      'gold_defect_pareto'
    )
),
row_counts AS (
  SELECT 'gold_manufacturing_daily' AS table_name, COUNT(*) AS actual, 1798 AS expected
  FROM manufacturing_intelligence.gold.gold_manufacturing_daily
  UNION ALL SELECT 'gold_factory_quality', COUNT(*), 543
  FROM manufacturing_intelligence.gold.gold_factory_quality
  UNION ALL SELECT 'gold_product_quality', COUNT(*), 1442
  FROM manufacturing_intelligence.gold.gold_product_quality
  UNION ALL SELECT 'gold_supplier_quality', COUNT(*), 8045
  FROM manufacturing_intelligence.gold.gold_supplier_quality
  UNION ALL SELECT 'gold_defect_pareto', COUNT(*), 8649
  FROM manufacturing_intelligence.gold.gold_defect_pareto
),
metric_violations AS (
  SELECT COUNT(*) AS actual
  FROM manufacturing_intelligence.gold.gold_manufacturing_daily
  WHERE ABS(fpy - pass_quantity / NULLIF(pass_quantity + fail_quantity, 0)) > 1e-12
     OR ABS(defect_rate - fail_quantity / NULLIF(production_quantity, 0)) > 1e-12
     OR ABS(dppm - fail_quantity * 1000000.0 / NULLIF(production_quantity, 0)) > 1e-6
     OR ABS(rework_rate - rework_quantity / NULLIF(production_quantity, 0)) > 1e-12
     OR ABS(scrap_rate - scrap_quantity / NULLIF(production_quantity, 0)) > 1e-12
),
inc_a_ranked AS (
  SELECT supplier_id, component_id, SUM(defective_units) AS defective_units,
         DENSE_RANK() OVER (ORDER BY SUM(defective_units) DESC) AS contribution_rank
  FROM manufacturing_intelligence.gold.gold_supplier_quality
  WHERE event_date BETWEEN DATE '2026-03-15' AND DATE '2026-04-12'
  GROUP BY supplier_id, component_id
),
inc_b_ranked AS (
  SELECT factory_id, line_id, defect_id, SUM(defect_quantity) AS defect_quantity,
         DENSE_RANK() OVER (ORDER BY SUM(defect_quantity) DESC) AS contribution_rank
  FROM manufacturing_intelligence.gold.gold_defect_pareto
  WHERE event_date BETWEEN DATE '2026-04-15' AND DATE '2026-05-05'
  GROUP BY factory_id, line_id, defect_id
),
inc_c_period AS (
  SELECT CASE
           WHEN production_date BETWEEN DATE '2026-02-01' AND DATE '2026-02-28' THEN 'early'
           WHEN production_date BETWEEN DATE '2026-05-01' AND DATE '2026-05-31' THEN 'late'
         END AS period,
         SUM(rework_quantity) / NULLIF(SUM(production_quantity), 0) AS rework_rate,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS fpy
  FROM manufacturing_intelligence.gold.gold_manufacturing_daily
  WHERE factory_id = 'FAC-MY' AND line_id = 'LINE-MY-03'
    AND (production_date BETWEEN DATE '2026-02-01' AND DATE '2026-02-28'
      OR production_date BETWEEN DATE '2026-05-01' AND DATE '2026-05-31')
  GROUP BY period
),
inc_c AS (
  SELECT
    MAX(CASE WHEN period = 'early' THEN rework_rate END) AS early_rework_rate,
    MAX(CASE WHEN period = 'late' THEN rework_rate END) AS late_rework_rate,
    MAX(CASE WHEN period = 'early' THEN fpy END) AS early_fpy,
    MAX(CASE WHEN period = 'late' THEN fpy END) AS late_fpy
  FROM inc_c_period
),
inc_d_ranked AS (
  SELECT factory_id, product_id, component_id, supplier_id, defect_id,
         SUM(defect_quantity) AS defect_quantity,
         DENSE_RANK() OVER (ORDER BY SUM(defect_quantity) DESC) AS contribution_rank
  FROM manufacturing_intelligence.gold.gold_defect_pareto
  WHERE event_date BETWEEN DATE '2026-05-10' AND DATE '2026-05-16'
  GROUP BY factory_id, product_id, component_id, supplier_id, defect_id
),
inc_e_month_product AS (
  SELECT date_trunc('month', production_date) AS production_month, product_id,
         SUM(production_quantity) AS production_quantity,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS product_fpy
  FROM manufacturing_intelligence.gold.gold_product_quality
  WHERE factory_id = 'FAC-MX'
    AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
  GROUP BY production_month, product_id
),
inc_e_aggregate AS (
  SELECT date_trunc('month', production_date) AS production_month,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS aggregate_fpy
  FROM manufacturing_intelligence.gold.gold_factory_quality
  WHERE factory_id = 'FAC-MX'
    AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
  GROUP BY production_month
),
inc_e AS (
  SELECT
    (SELECT aggregate_fpy FROM inc_e_aggregate
      WHERE production_month = DATE '2026-05-01') AS may_fpy,
    (SELECT aggregate_fpy FROM inc_e_aggregate
      WHERE production_month = DATE '2026-06-01') AS june_fpy,
    (SELECT AVG(ABS(june.product_fpy - may.product_fpy))
      FROM inc_e_month_product may
      JOIN inc_e_month_product june USING (product_id)
      WHERE may.production_month = DATE '2026-05-01'
        AND june.production_month = DATE '2026-06-01') AS mean_abs_product_fpy_change,
    (SELECT production_quantity FROM inc_e_month_product
      WHERE production_month = DATE '2026-05-01' AND product_id = 'PROD-X100') AS may_x100_volume,
    (SELECT production_quantity FROM inc_e_month_product
      WHERE production_month = DATE '2026-06-01' AND product_id = 'PROD-X100') AS june_x100_volume,
    (SELECT production_quantity FROM inc_e_month_product
      WHERE production_month = DATE '2026-05-01' AND product_id = 'PROD-X200') AS may_x200_volume,
    (SELECT production_quantity FROM inc_e_month_product
      WHERE production_month = DATE '2026-06-01' AND product_id = 'PROD-X200') AS june_x200_volume
)
SELECT 'gold_table_inventory' AS check_name,
       IF(actual = 5, 'PASS', 'FAIL') AS status,
       CAST(actual AS STRING) AS actual, '5' AS expected,
       'Tableau may read exactly the five governed Gold sources' AS detail
FROM required_tables
UNION ALL
SELECT CONCAT('row_count_', table_name),
       IF(actual = expected, 'PASS', 'FAIL'),
       CAST(actual AS STRING), CAST(expected AS STRING),
       'Seed-42 deployed Gold row count'
FROM row_counts
UNION ALL
SELECT 'governed_metric_formulas',
       IF(actual = 0, 'PASS', 'FAIL'),
       CAST(actual AS STRING), '0',
       'Rows whose stored Gold rate differs from its additive numerator/denominator'
FROM metric_violations
UNION ALL
SELECT 'incident_a_supplier_power_module',
       IF(COALESCE(MAX(contribution_rank), 999) <= 3, 'PASS', 'FAIL'),
       CAST(COALESCE(MAX(contribution_rank), 999) AS STRING), '<= 3',
       'SUP-B + COMP-PWR is a leading contribution during Incident A'
FROM inc_a_ranked WHERE supplier_id = 'SUP-B' AND component_id = 'COMP-PWR'
UNION ALL
SELECT 'incident_b_mexico_line2_voltage',
       IF(COALESCE(MAX(contribution_rank), 999) <= 3, 'PASS', 'FAIL'),
       CAST(COALESCE(MAX(contribution_rank), 999) AS STRING), '<= 3',
       'FAC-MX + LINE-MX-02 + DEF-VOLT is a leading contribution during Incident B'
FROM inc_b_ranked
WHERE factory_id = 'FAC-MX' AND line_id = 'LINE-MX-02' AND defect_id = 'DEF-VOLT'
UNION ALL
SELECT 'incident_c_ramp_line_improves',
       IF(early_rework_rate > late_rework_rate AND early_fpy < late_fpy, 'PASS', 'FAIL'),
       CONCAT('early_rework=', CAST(early_rework_rate AS STRING),
              ', late_rework=', CAST(late_rework_rate AS STRING),
              ', early_fpy=', CAST(early_fpy AS STRING),
              ', late_fpy=', CAST(late_fpy AS STRING)),
       'early rework > late rework and early FPY < late FPY',
       'Malaysia ramp line improves over the learning period'
FROM inc_c
UNION ALL
SELECT 'incident_d_localized_memory_failure',
       IF(COALESCE(MAX(contribution_rank), 999) <= 3, 'PASS', 'FAIL'),
       CAST(COALESCE(MAX(contribution_rank), 999) AS STRING), '<= 3',
       'FAC-TW + PROD-X200 + COMP-MEM + SUP-C + DEF-MEM is a leading Gold symptom'
FROM inc_d_ranked
WHERE factory_id = 'FAC-TW' AND product_id = 'PROD-X200'
  AND component_id = 'COMP-MEM' AND supplier_id = 'SUP-C' AND defect_id = 'DEF-MEM'
UNION ALL
SELECT 'incident_e_aggregate_fpy_declines',
       IF(june_fpy < may_fpy, 'PASS', 'FAIL'),
       CONCAT('May=', CAST(may_fpy AS STRING), ', June=', CAST(june_fpy AS STRING)),
       'June < May',
       'Mexico aggregate FPY declines after the mix shift'
FROM inc_e
UNION ALL
SELECT 'incident_e_product_fpy_stable',
       IF(mean_abs_product_fpy_change < 0.035, 'PASS', 'FAIL'),
       CAST(mean_abs_product_fpy_change AS STRING), '< 0.035',
       'Mean absolute within-product FPY change remains within the governed tolerance'
FROM inc_e
UNION ALL
SELECT 'incident_e_product_mix_shift',
       IF(june_x100_volume < may_x100_volume AND june_x200_volume > may_x200_volume,
          'PASS', 'FAIL'),
       CONCAT('X100 ', CAST(may_x100_volume AS STRING), '→', CAST(june_x100_volume AS STRING),
              '; X200 ', CAST(may_x200_volume AS STRING), '→', CAST(june_x200_volume AS STRING)),
       'X100 decreases and X200 increases',
       'Volume shift explains why aggregate FPY must not be labeled broad deterioration'
FROM inc_e
ORDER BY check_name;
