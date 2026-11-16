SELECT * FROM {{ ref('int_ml_order_events') }}
WHERE order_id IS NULL OR customer_unique_id IS NULL OR TRIM(customer_unique_id) = ''
   OR purchase_at IS NULL OR placed_item_value_brl IS NULL
   OR invalid_price_count > 0 OR item_count < 1
