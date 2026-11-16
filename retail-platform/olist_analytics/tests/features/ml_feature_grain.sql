SELECT customer_unique_id, feature_timestamp, COUNT(*) AS copies
FROM {{ ref('customer_features_monthly') }}
GROUP BY 1,2 HAVING COUNT(*) <> 1
