WITH c AS(SELECT DISTINCT feature_timestamp AS ts FROM {{ ref('customer_features_monthly') }}),
p AS(SELECT DISTINCT feature_timestamp AS ts FROM {{ ref('product_features_monthly') }})
SELECT COALESCE(c.ts,p.ts) AS missing_cutoff FROM c FULL OUTER JOIN p USING(ts)
WHERE c.ts IS NULL OR p.ts IS NULL
