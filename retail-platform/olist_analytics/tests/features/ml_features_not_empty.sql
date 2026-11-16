SELECT COUNT(*) AS feature_rows FROM {{ ref('customer_features_monthly') }}
HAVING COUNT(*) = 0
