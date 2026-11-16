SELECT DISTINCT c.customer_unique_id
FROM {{ ref('stg_customers') }} AS c
JOIN {{ ref('stg_orders') }} AS o USING (customer_id)
LEFT JOIN {{ ref('dim_customer_history') }} AS h USING (customer_unique_id)
WHERE c.customer_unique_id IS NOT NULL
  AND o.order_purchase_at IS NOT NULL
  AND h.customer_version_key IS NULL
