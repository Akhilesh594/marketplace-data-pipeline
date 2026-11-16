{{ config(materialized='view') }}

SELECT
    order_id,
    customer_id,
    LOWER(TRIM(order_status)) AS order_status,
    SAFE_CAST(order_purchase_timestamp AS DATETIME)
        AS order_purchase_at,
    SAFE_CAST(order_approved_at AS DATETIME)
        AS order_approved_at,
    SAFE_CAST(order_delivered_carrier_date AS DATETIME)
        AS handed_to_carrier_at,
    SAFE_CAST(order_delivered_customer_date AS DATETIME)
        AS delivered_to_customer_at,
    SAFE_CAST(order_estimated_delivery_date AS DATETIME)
        AS estimated_delivery_at
FROM {{ source('olist', 'orders') }}