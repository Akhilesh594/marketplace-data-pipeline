{{ config(materialized='table') }}

WITH sales AS (
    SELECT
        SUM(item_price) AS revenue_brl,
        COUNT(DISTINCT order_id) AS order_count,
        COUNT(*) AS item_count
    FROM {{ ref('fact_sales_history') }}
    WHERE order_status = 'delivered'
),
customers AS (
    SELECT COUNT(*) AS customer_count,
        COUNTIF(order_count >= 2) AS repeat_customer_count
    FROM {{ ref('metrics_customer_summary') }}
)
SELECT
    s.*,
    c.*,
    SAFE_DIVIDE(s.revenue_brl, s.order_count) AS average_order_value_brl,
    SAFE_DIVIDE(c.repeat_customer_count, c.customer_count) AS repeat_customer_rate,
    CAST(NULL AS NUMERIC) AS margin_brl,
    'Unavailable: source has no product costs' AS margin_note
FROM sales AS s CROSS JOIN customers AS c
