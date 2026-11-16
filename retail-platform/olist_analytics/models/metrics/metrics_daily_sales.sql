{{ config(materialized='table') }}

SELECT
    DATE(order_purchase_at) AS sales_date,
    SUM(item_price) AS revenue_brl,
    SUM(freight_value) AS freight_brl,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_unique_id) AS customer_count,
    COUNT(*) AS item_count,
    SAFE_DIVIDE(SUM(item_price), COUNT(DISTINCT order_id)) AS average_order_value_brl
FROM {{ ref('fact_sales_history') }}
WHERE order_status = 'delivered'
GROUP BY sales_date
