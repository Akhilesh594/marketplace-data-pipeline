{{ config(materialized='table') }}

-- Full dataset lifetime summary; not a point-in-time ML feature.
SELECT
    customer_unique_id,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(item_price) AS total_spend_brl,
    MIN(order_purchase_at) AS first_purchase_at,
    MAX(order_purchase_at) AS last_purchase_at
FROM {{ ref('fact_sales_history') }}
WHERE order_status = 'delivered'
GROUP BY customer_unique_id
