-- PR #12 Tableau MVP reconciliation. Apply identical filters in Tableau and SQL.

-- Executive Overview: unfiltered governed KPI baseline.
SELECT
  SUM(production_quantity) AS production_quantity,
  SUM(pass_quantity) AS pass_quantity,
  SUM(fail_quantity) AS fail_quantity,
  SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS fpy,
  SUM(fail_quantity) / NULLIF(SUM(production_quantity), 0) AS defect_rate,
  SUM(fail_quantity) * 1000000.0 / NULLIF(SUM(production_quantity), 0) AS dppm,
  SUM(rework_quantity) / NULLIF(SUM(production_quantity), 0) AS rework_rate,
  SUM(scrap_quantity) / NULLIF(SUM(production_quantity), 0) AS scrap_rate
FROM manufacturing_intelligence.gold.gold_manufacturing_daily;

-- Weekly weighted FPY; Tableau must not average daily FPY.
SELECT reporting_year, reporting_week,
       SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS fpy
FROM manufacturing_intelligence.gold.gold_manufacturing_daily
GROUP BY reporting_year, reporting_week
ORDER BY reporting_year, reporting_week;

-- Root-cause contribution baselines.
SELECT defect_id, defect_name, SUM(defect_quantity) AS defect_quantity
FROM manufacturing_intelligence.gold.gold_defect_pareto
GROUP BY defect_id, defect_name
ORDER BY defect_quantity DESC;

SELECT component_id, component_name, supplier_id, supplier_name,
       SUM(defective_units) AS defective_units,
       SUM(defective_units) / NULLIF(SUM(inspected_units), 0) AS attributed_defect_rate
FROM manufacturing_intelligence.gold.gold_supplier_quality
GROUP BY component_id, component_name, supplier_id, supplier_name
ORDER BY defective_units DESC;

-- Incident E: monthly aggregate FPY and recomputed product mix.
WITH product_month AS (
  SELECT date_trunc('month', production_date) AS production_month,
         factory_id, product_id,
         SUM(production_quantity) AS production_quantity,
         SUM(pass_quantity) AS pass_quantity,
         SUM(fail_quantity) AS fail_quantity
  FROM manufacturing_intelligence.gold.gold_product_quality
  WHERE factory_id = 'FAC-MX'
    AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
  GROUP BY production_month, factory_id, product_id
), scored AS (
  SELECT *,
         pass_quantity / NULLIF(pass_quantity + fail_quantity, 0) AS product_fpy,
         production_quantity / NULLIF(SUM(production_quantity) OVER (
           PARTITION BY production_month, factory_id), 0) AS product_mix_share
  FROM product_month
)
SELECT production_month, product_id, production_quantity, product_mix_share, product_fpy
FROM scored
ORDER BY production_month, product_id;

SELECT date_trunc('month', production_date) AS production_month,
       SUM(pass_quantity) / NULLIF(SUM(pass_quantity + fail_quantity), 0) AS aggregate_fpy
FROM manufacturing_intelligence.gold.gold_factory_quality
WHERE factory_id = 'FAC-MX'
  AND production_date BETWEEN DATE '2026-05-01' AND DATE '2026-06-30'
GROUP BY production_month
ORDER BY production_month;

-- Gold-only boundary check for Tableau data sources.
SELECT table_name
FROM manufacturing_intelligence.information_schema.tables
WHERE table_schema = 'gold'
  AND table_name IN (
    'gold_manufacturing_daily',
    'gold_factory_quality',
    'gold_product_quality',
    'gold_supplier_quality',
    'gold_defect_pareto'
  )
ORDER BY table_name;
