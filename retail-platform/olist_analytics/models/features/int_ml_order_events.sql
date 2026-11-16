{{ config(materialized='view') }}
-- Event-time approximation: order/item attributes assumed known at purchase.
-- Never filter on final order_status or use future delivery/review outcomes.
WITH items AS (
    SELECT order_id, SUM(price) AS placed_item_value_brl, COUNT(*) AS item_count,
        COUNTIF(price IS NULL OR price < 0) AS invalid_price_count
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
)
SELECT o.order_id, c.customer_unique_id, o.order_purchase_at AS purchase_at,
    i.placed_item_value_brl, i.item_count, i.invalid_price_count
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_customers') }} c USING (customer_id)
JOIN items i USING (order_id)
