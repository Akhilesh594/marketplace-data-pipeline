WITH sample AS (
 SELECT * FROM {{ ref('customer_features_monthly') }}
 QUALIFY ROW_NUMBER() OVER (ORDER BY feature_timestamp DESC, customer_unique_id) <= 100
), expected AS (
 SELECT f.customer_unique_id, f.feature_timestamp, f.orders_90d, f.placed_item_value_90d_brl,
     COUNT(e.order_id) AS expected_count, COALESCE(SUM(e.placed_item_value_brl),0) AS expected_value
 FROM sample f LEFT JOIN {{ ref('int_ml_order_events') }} e
 ON f.customer_unique_id=e.customer_unique_id
 AND e.purchase_at >= DATETIME_SUB(f.cutoff_local, INTERVAL 90 DAY)
 AND e.purchase_at < f.cutoff_local
 GROUP BY 1,2,3,4
)
SELECT * FROM expected
WHERE orders_90d != expected_count OR ABS(placed_item_value_90d_brl - CAST(expected_value AS FLOAT64)) > 0.01
