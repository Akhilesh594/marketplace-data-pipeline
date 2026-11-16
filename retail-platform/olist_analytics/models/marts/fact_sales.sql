{{ config(materialized='table') }}

-- Grain: one order item, identified by order_id + order_item_id.
-- No payments/reviews join here: those can have multiple rows per order.
-- All source order statuses are retained; reporting must choose eligible statuses.
SELECT
    TO_HEX(SHA256(CONCAT(i.order_id, '|', CAST(i.order_item_id AS STRING))))
        AS sale_key,
    i.order_id,
    i.order_item_id,
    o.customer_id AS customer_key,
    i.product_id AS product_key,
    i.seller_id AS store_key,
    CAST(FORMAT_DATE('%Y%m%d', DATE(o.order_purchase_at)) AS INT64) AS date_key,
    o.order_status,
    o.order_purchase_at,
    o.delivered_to_customer_at,
    i.price AS item_price,
    i.freight_value,
    i.price + i.freight_value AS item_value_including_freight
FROM {{ ref('stg_order_items') }} AS i
LEFT JOIN {{ ref('stg_orders') }} AS o ON i.order_id = o.order_id
