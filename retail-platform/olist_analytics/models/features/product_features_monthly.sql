{{ config(materialized='table', cluster_by=['product_id']) }}
-- Original timestamps; placed orders, no final-status filtering or future outcomes.
WITH cutoffs AS (
 SELECT DISTINCT cutoff_local FROM {{ ref('customer_features_monthly') }}
), events AS (
 SELECT e.order_id,e.purchase_at,i.product_id,i.price
 FROM {{ ref('int_ml_order_events') }} e
 JOIN {{ ref('stg_order_items') }} i USING(order_id)
), aggregated AS (
 SELECT e.product_id,c.cutoff_local,
 COUNT(DISTINCT IF(e.purchase_at >= DATETIME_SUB(c.cutoff_local,INTERVAL 30 DAY),e.order_id,NULL)) AS orders_30d,
 COUNT(DISTINCT IF(e.purchase_at >= DATETIME_SUB(c.cutoff_local,INTERVAL 90 DAY),e.order_id,NULL)) AS orders_90d,
 COUNTIF(e.purchase_at >= DATETIME_SUB(c.cutoff_local,INTERVAL 30 DAY)) AS units_30d,
 COUNTIF(e.purchase_at >= DATETIME_SUB(c.cutoff_local,INTERVAL 90 DAY)) AS units_90d,
 SUM(IF(e.purchase_at >= DATETIME_SUB(c.cutoff_local,INTERVAL 90 DAY),e.price,0)) AS placed_item_value_90d_brl,
 MAX(e.purchase_at) AS last_order_at
 FROM cutoffs c JOIN events e ON e.purchase_at<c.cutoff_local
 GROUP BY e.product_id,c.cutoff_local
)
SELECT product_id,TIMESTAMP(cutoff_local,'America/Sao_Paulo') AS feature_timestamp,
 cutoff_local,orders_30d,orders_90d,units_30d,units_90d,
 CAST(placed_item_value_90d_brl AS FLOAT64) AS placed_item_value_90d_brl,
 CAST(COALESCE(SAFE_DIVIDE(placed_item_value_90d_brl,units_90d),0) AS FLOAT64) AS average_item_price_90d_brl,
 DATETIME_DIFF(cutoff_local,last_order_at,DAY) AS days_since_last_order,last_order_at
FROM aggregated
