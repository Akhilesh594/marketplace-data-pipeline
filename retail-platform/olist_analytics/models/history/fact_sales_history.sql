{{ config(materialized='table') }}

-- Match the sale to the customer version observed at its purchase time.
SELECT
    f.*,
    c.customer_unique_id,
    h.customer_version_key
FROM {{ ref('fact_sales') }} AS f
LEFT JOIN {{ ref('dim_customer') }} AS c USING (customer_key)
LEFT JOIN {{ ref('dim_customer_history') }} AS h
    ON c.customer_unique_id = h.customer_unique_id
    AND f.order_purchase_at >= h.valid_from
    AND (f.order_purchase_at < h.valid_to OR h.valid_to IS NULL)
