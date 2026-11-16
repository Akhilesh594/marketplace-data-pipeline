SELECT * FROM {{ ref('customer_features_monthly') }}
WHERE customer_unique_id IS NULL OR feature_timestamp IS NULL
 OR orders_30d IS NULL OR orders_90d IS NULL OR orders_lifetime IS NULL
 OR orders_30d < 0 OR orders_30d > orders_90d OR orders_90d > orders_lifetime
 OR orders_lifetime < 1 OR days_since_last_order IS NULL OR days_since_last_order < 0
 OR customer_age_days IS NULL OR customer_age_days < days_since_last_order
 OR placed_item_value_90d_brl IS NULL OR placed_item_value_90d_brl < 0
 OR average_order_value_90d_brl IS NULL OR average_order_value_90d_brl < 0
 OR ABS(average_order_value_90d_brl - COALESCE(SAFE_DIVIDE(placed_item_value_90d_brl, orders_90d), 0)) > 0.00001
