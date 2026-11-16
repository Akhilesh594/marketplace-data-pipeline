SELECT * FROM {{ ref('product_features_monthly') }}
WHERE product_id IS NULL OR TRIM(product_id)='' OR feature_timestamp IS NULL
 OR orders_30d IS NULL OR orders_90d IS NULL OR units_30d IS NULL OR units_90d IS NULL
 OR orders_30d<0 OR orders_30d>orders_90d OR orders_30d>units_30d OR orders_90d>units_90d
 OR units_30d<0 OR units_30d>units_90d
 OR placed_item_value_90d_brl IS NULL OR placed_item_value_90d_brl<0
 OR average_item_price_90d_brl IS NULL OR average_item_price_90d_brl<0
 OR ABS(average_item_price_90d_brl-COALESCE(SAFE_DIVIDE(placed_item_value_90d_brl,units_90d),0))>0.00001
 OR days_since_last_order IS NULL OR days_since_last_order<0
 OR last_order_at IS NULL OR last_order_at>=cutoff_local
 OR feature_timestamp!=TIMESTAMP(cutoff_local,'America/Sao_Paulo')
