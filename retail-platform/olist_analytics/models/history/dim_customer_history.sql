{{ config(materialized='table') }}

-- Observation-based Type 2 history, not verified customer move dates.
-- When profiles conflict at exactly the same timestamp, customer_id breaks ties.
WITH events AS (
    SELECT
        c.customer_unique_id,
        c.customer_id AS observed_customer_id,
        c.customer_zip_code_prefix AS zip_code_prefix,
        c.customer_city AS city,
        c.customer_state AS state,
        o.order_purchase_at AS observed_at,
        TO_HEX(SHA256(TO_JSON_STRING(STRUCT(
            c.customer_zip_code_prefix AS zip_code_prefix,
            c.customer_city AS city,
            c.customer_state AS state
        )))) AS attribute_hash
    FROM {{ ref('stg_orders') }} AS o
    JOIN {{ ref('stg_customers') }} AS c USING (customer_id)
    WHERE c.customer_unique_id IS NOT NULL AND o.order_purchase_at IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY c.customer_unique_id, o.order_purchase_at
        ORDER BY c.customer_id DESC
    ) = 1
),
compared AS (
    SELECT *,
        LAG(attribute_hash) OVER (
            PARTITION BY customer_unique_id ORDER BY observed_at
        ) AS previous_hash
    FROM events
),
changes AS (
    SELECT * EXCEPT(previous_hash)
    FROM compared
    WHERE previous_hash IS NULL OR attribute_hash != previous_hash
),
versions AS (
    SELECT *,
        observed_at AS valid_from,
        LEAD(observed_at) OVER (
            PARTITION BY customer_unique_id ORDER BY observed_at
        ) AS valid_to,
        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id ORDER BY observed_at
        ) AS version_number
    FROM changes
)
SELECT
    TO_HEX(SHA256(CONCAT(
        customer_unique_id, '|',
        FORMAT_DATETIME('%Y-%m-%d %H:%M:%E6S', valid_from)
    ))) AS customer_version_key,
    customer_unique_id,
    observed_customer_id,
    zip_code_prefix,
    city,
    state,
    valid_from,
    valid_to,
    valid_to IS NULL AS is_current,
    version_number
FROM versions
