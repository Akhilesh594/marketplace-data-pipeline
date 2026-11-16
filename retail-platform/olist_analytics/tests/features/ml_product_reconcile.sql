WITH sample AS (
 SELECT * FROM {{ ref('product_features_monthly') }}
 QUALIFY ROW_NUMBER() OVER(ORDER BY feature_timestamp DESC,product_id)<=100
), expected AS (
 SELECT f.product_id,f.feature_timestamp,f.orders_90d,f.units_90d,f.placed_item_value_90d_brl,
 COUNT(DISTINCT e.order_id) AS expected_orders,COUNT(e.order_id) AS expected_units,
 COALESCE(SUM(e.price),0) AS expected_value
 FROM sample f LEFT JOIN (
 SELECT e.order_id,e.purchase_at,i.product_id,i.price FROM {{ ref('int_ml_order_events') }} e
 JOIN {{ ref('stg_order_items') }} i USING(order_id)
 ) e ON f.product_id=e.product_id
 AND e.purchase_at>=DATETIME_SUB(f.cutoff_local,INTERVAL 90 DAY) AND e.purchase_at<f.cutoff_local
 GROUP BY 1,2,3,4,5
)
SELECT * FROM expected WHERE orders_90d!=expected_orders OR units_90d!=expected_units
 OR ABS(placed_item_value_90d_brl-CAST(expected_value AS FLOAT64))>0.01
