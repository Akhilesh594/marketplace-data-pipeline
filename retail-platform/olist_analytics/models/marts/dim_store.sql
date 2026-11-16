{{ config(materialized='table') }}

-- Olist is a marketplace. A seller is our documented store equivalent.
SELECT
    seller_id AS store_key,
    seller_id,
    seller_zip_code_prefix AS zip_code_prefix,
    seller_city AS city,
    seller_state AS state
FROM {{ ref('stg_sellers') }}
