SELECT order_id, payment_sequential, COUNT(*) AS occurrences
FROM {{ ref('stg_order_payments') }}
GROUP BY order_id, payment_sequential
HAVING COUNT(*) > 1
