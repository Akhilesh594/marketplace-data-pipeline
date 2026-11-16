SELECT COUNT(*) AS feature_rows FROM {{ ref('product_features_monthly') }} HAVING COUNT(*)=0
