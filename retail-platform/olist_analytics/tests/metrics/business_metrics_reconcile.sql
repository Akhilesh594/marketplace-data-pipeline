WITH totals AS (
    SELECT COALESCE(SUM(revenue_brl), 0) AS revenue, SUM(order_count) AS orders
    FROM {{ ref('metrics_daily_sales') }}
)
SELECT 'business_metrics_mismatch' AS issue
FROM totals AS t CROSS JOIN {{ ref('metrics_business_summary') }} AS b
WHERE t.revenue != b.revenue_brl OR t.orders != b.order_count
   OR b.repeat_customer_rate < 0 OR b.repeat_customer_rate > 1
