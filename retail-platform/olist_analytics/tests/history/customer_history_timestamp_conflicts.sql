{{ config(severity='warn') }}

-- Surface simultaneous differing profiles; the model uses a deterministic tie-break.
SELECT c.customer_unique_id, o.order_purchase_at
FROM {{ ref('stg_customers') }} AS c
JOIN {{ ref('stg_orders') }} AS o USING (customer_id)
WHERE c.customer_unique_id IS NOT NULL AND o.order_purchase_at IS NOT NULL
GROUP BY c.customer_unique_id, o.order_purchase_at
HAVING COUNT(DISTINCT TO_JSON_STRING(STRUCT(
    c.customer_zip_code_prefix, c.customer_city, c.customer_state
))) > 1
