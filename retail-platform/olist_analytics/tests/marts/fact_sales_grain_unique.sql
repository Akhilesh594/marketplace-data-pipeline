SELECT order_id, order_item_id, COUNT(*) AS occurrences
FROM {{ ref('fact_sales') }}
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1
