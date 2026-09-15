-- Every query must return zero rows, except the inventory and signal evidence queries.
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

SELECT table_schema, table_name
FROM manufacturing_intelligence.information_schema.tables
WHERE table_schema IN ('silver', 'gold') ORDER BY table_schema, table_name;

-- Incident E: aggregate Mexico FPY falls in June while product-level FPY remains available.
SELECT production_date, factory_id, product_id, production_quantity, fpy, product_mix_share
FROM manufacturing_intelligence.gold.gold_product_quality
WHERE factory_id = 'FAC-MX' AND production_date BETWEEN DATE '2026-05-06' AND DATE '2026-06-30'
ORDER BY production_date, product_id;

