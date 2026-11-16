{{ config(materialized='table') }}

-- One row per source customer_id (an order-associated customer profile).
-- customer_unique_id identifies repeat customers across orders.
SELECT
    customer_id AS customer_key,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix AS zip_code_prefix,
    customer_city AS city,
    customer_state AS state
FROM {{ ref('stg_customers') }}
