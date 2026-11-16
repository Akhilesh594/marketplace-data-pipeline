SELECT customer_unique_id
FROM {{ ref('dim_customer_history') }}
GROUP BY customer_unique_id
HAVING COUNTIF(is_current) != 1 OR COUNTIF(valid_to IS NULL) != 1
