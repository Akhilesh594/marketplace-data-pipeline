SELECT order_id, order_item_id, COUNT(*) AS occurrences
FROM {{ ref('stg_order_items') }}
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1
