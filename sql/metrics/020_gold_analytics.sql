-- Additive measures are retained so Tableau can recompute governed rates after filtering.
CREATE OR REPLACE TABLE manufacturing_intelligence.gold.gold_manufacturing_daily USING DELTA AS
WITH daily AS (
  SELECT production_date, factory_id, line_id, product_id,
         SUM(completed_qty) AS production_quantity,
         SUM(first_pass_pass_qty) AS pass_quantity, SUM(fail_qty) AS fail_quantity,
         SUM(rework_qty) AS rework_quantity, SUM(scrap_qty) AS scrap_quantity
  FROM manufacturing_intelligence.silver.silver_fact_production
  GROUP BY production_date, factory_id, line_id, product_id
), metric_ready AS (
  SELECT *, pass_quantity / NULLIF(pass_quantity + fail_quantity, 0) AS fpy,
         fail_quantity / NULLIF(production_quantity, 0) AS defect_rate,
         fail_quantity * 1000000.0 / NULLIF(production_quantity, 0) AS dppm,
         rework_quantity / NULLIF(production_quantity, 0) AS rework_rate,
         scrap_quantity / NULLIF(production_quantity, 0) AS scrap_rate,
         1.0 - pass_quantity / NULLIF(pass_quantity + fail_quantity, 0) AS yield_loss
  FROM daily
), weekly AS (
  SELECT factory_id, line_id, product_id, year(production_date) AS reporting_year,
         weekofyear(production_date) AS reporting_week,
         SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS week_fpy
  FROM metric_ready
  GROUP BY factory_id, line_id, product_id, year(production_date), weekofyear(production_date)
), weekly_change AS (
  SELECT *, week_fpy - LAG(week_fpy) OVER (
         PARTITION BY factory_id, line_id, product_id ORDER BY reporting_year, reporting_week
       ) AS wow_fpy_change
  FROM weekly
)
SELECT d.*, w.reporting_year, w.reporting_week, w.week_fpy, w.wow_fpy_change,
       current_timestamp() AS _gold_updated_at
FROM metric_ready d
JOIN weekly_change w ON d.factory_id = w.factory_id AND d.line_id = w.line_id
 AND d.product_id = w.product_id AND year(d.production_date) = w.reporting_year
 AND weekofyear(d.production_date) = w.reporting_week;

CREATE OR REPLACE TABLE manufacturing_intelligence.gold.gold_factory_quality USING DELTA AS
SELECT p.production_date, p.factory_id, f.factory_name, f.country,
       SUM(p.completed_qty) AS production_quantity,
       SUM(p.first_pass_pass_qty) AS pass_quantity, SUM(p.fail_qty) AS fail_quantity,
       SUM(p.first_pass_pass_qty) / NULLIF(SUM(p.first_pass_pass_qty + p.fail_qty), 0) AS fpy,
       SUM(p.fail_qty) * 1000000.0 / NULLIF(SUM(p.completed_qty), 0) AS dppm,
       SUM(p.rework_qty) / NULLIF(SUM(p.completed_qty), 0) AS rework_rate,
       SUM(p.scrap_qty) / NULLIF(SUM(p.completed_qty), 0) AS scrap_rate
FROM manufacturing_intelligence.silver.silver_fact_production p
JOIN manufacturing_intelligence.silver.silver_dim_factory f ON p.factory_id = f.factory_id
GROUP BY p.production_date, p.factory_id, f.factory_name, f.country;

CREATE OR REPLACE TABLE manufacturing_intelligence.gold.gold_product_quality USING DELTA AS
SELECT p.production_date, p.factory_id, p.product_id, pr.product_name, pr.product_family,
       SUM(p.completed_qty) AS production_quantity,
       SUM(p.first_pass_pass_qty) AS pass_quantity, SUM(p.fail_qty) AS fail_quantity,
       SUM(p.first_pass_pass_qty) / NULLIF(SUM(p.first_pass_pass_qty + p.fail_qty), 0) AS fpy,
       SUM(p.completed_qty) / NULLIF(SUM(SUM(p.completed_qty)) OVER (
         PARTITION BY p.production_date, p.factory_id), 0) AS product_mix_share,
       SUM(p.fail_qty) * 1000000.0 / NULLIF(SUM(p.completed_qty), 0) AS dppm
FROM manufacturing_intelligence.silver.silver_fact_production p
JOIN manufacturing_intelligence.silver.silver_dim_product pr ON p.product_id = pr.product_id
GROUP BY p.production_date, p.factory_id, p.product_id, pr.product_name, pr.product_family;

CREATE OR REPLACE TABLE manufacturing_intelligence.gold.gold_supplier_quality USING DELTA AS
WITH attributed AS (
  SELECT q.event_date, q.factory_id, q.product_id, q.component_id, q.supplier_id,
         q.production_lot_id, SUM(q.event_quantity) AS defective_units
  FROM manufacturing_intelligence.silver.silver_fact_quality_event q
  WHERE q.is_supplier_attributed AND q.is_first_pass_failure
  GROUP BY q.event_date, q.factory_id, q.product_id, q.component_id, q.supplier_id,
           q.production_lot_id
), lot_denominator AS (
  SELECT a.event_date, a.factory_id, a.product_id, a.component_id, a.supplier_id,
         SUM(a.defective_units) AS defective_units,
         SUM(p.completed_qty) AS inspected_units
  FROM attributed a
  JOIN manufacturing_intelligence.silver.silver_fact_production p
    ON a.production_lot_id = p.production_lot_id
  GROUP BY a.event_date, a.factory_id, a.product_id, a.component_id, a.supplier_id
)
SELECT d.*, s.supplier_name, c.component_name,
       d.defective_units / NULLIF(d.inspected_units, 0) AS supplier_attributed_defect_rate,
       d.defective_units * 1000000.0 / NULLIF(d.inspected_units, 0) AS supplier_attributed_dppm
FROM lot_denominator d
JOIN manufacturing_intelligence.silver.silver_dim_supplier s ON d.supplier_id = s.supplier_id
JOIN manufacturing_intelligence.silver.silver_dim_component c ON d.component_id = c.component_id;

CREATE OR REPLACE TABLE manufacturing_intelligence.gold.gold_defect_pareto USING DELTA AS
WITH defects AS (
  SELECT q.event_date, q.factory_id, q.line_id, q.product_id, q.component_id, q.supplier_id,
         q.defect_id, d.defect_name, d.defect_category,
         SUM(CASE WHEN q.is_first_pass_failure THEN q.event_quantity ELSE 0 END) AS defect_quantity
  FROM manufacturing_intelligence.silver.silver_fact_quality_event q
  JOIN manufacturing_intelligence.silver.silver_dim_defect d ON q.defect_id = d.defect_id
  GROUP BY q.event_date, q.factory_id, q.line_id, q.product_id, q.component_id, q.supplier_id,
           q.defect_id, d.defect_name, d.defect_category
), ranked AS (
  SELECT *, SUM(defect_quantity) OVER (PARTITION BY event_date, factory_id) AS total_failures,
         SUM(defect_quantity) OVER (PARTITION BY event_date, factory_id ORDER BY defect_quantity DESC,
           defect_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_failures,
         dense_rank() OVER (PARTITION BY event_date, factory_id ORDER BY defect_quantity DESC) AS pareto_rank
  FROM defects
)
SELECT *, defect_quantity / NULLIF(total_failures, 0) AS defect_contribution,
       cumulative_failures / NULLIF(total_failures, 0) AS cumulative_defect_contribution
FROM ranked;
