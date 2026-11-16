{{ config(materialized='view') }}

SELECT
    order_id,
    SAFE_CAST(payment_sequential AS INT64) AS payment_sequential,
    LOWER(TRIM(payment_type)) AS payment_type,
    SAFE_CAST(payment_installments AS INT64) AS payment_installments,
    SAFE_CAST(payment_value AS NUMERIC) AS payment_value
FROM {{ source('olist', 'order_payments') }}
