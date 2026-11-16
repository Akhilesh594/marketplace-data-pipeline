SELECT COUNT(*) AS event_rows FROM {{ ref('int_ml_order_events') }} HAVING COUNT(*)=0
