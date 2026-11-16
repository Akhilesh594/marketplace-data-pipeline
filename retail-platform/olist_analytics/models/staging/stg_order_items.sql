{{ config(materialized='view') }}

SELECT
    order_id,
    SAFE_CAST(order_item_id AS INT64) AS order_item_id,
    product_id,
    seller_id,
    SAFE_CAST(shipping_limit_date AS DATETIME) AS shipping_limit_at,
    SAFE_CAST(price AS NUMERIC) AS price,
    SAFE_CAST(freight_value AS NUMERIC) AS freight_value
FROM {{ source('olist', 'order_items') }}
