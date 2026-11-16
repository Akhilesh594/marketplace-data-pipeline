SELECT 'order_items' AS table_name, order_id
FROM {{ ref('stg_order_items') }}
WHERE price < 0 OR freight_value < 0
UNION ALL
SELECT 'order_payments' AS table_name, order_id
FROM {{ ref('stg_order_payments') }}
WHERE payment_value < 0
