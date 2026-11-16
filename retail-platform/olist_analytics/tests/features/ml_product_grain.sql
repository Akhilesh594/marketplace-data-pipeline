SELECT product_id,feature_timestamp,COUNT(*) AS copies FROM {{ ref('product_features_monthly') }} GROUP BY 1,2 HAVING COUNT(*)<>1
