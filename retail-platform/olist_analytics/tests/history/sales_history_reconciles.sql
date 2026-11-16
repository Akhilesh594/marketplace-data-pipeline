WITH original AS (
    SELECT COUNT(*) AS row_count, COALESCE(SUM(item_price), 0) AS sales
    FROM {{ ref('fact_sales') }}
), historical AS (
    SELECT COUNT(*) AS row_count, COALESCE(SUM(item_price), 0) AS sales
    FROM {{ ref('fact_sales_history') }}
)
SELECT 'history_join_changed_sales' AS issue
FROM original AS o CROSS JOIN historical AS h
WHERE o.row_count != h.row_count OR o.sales != h.sales
