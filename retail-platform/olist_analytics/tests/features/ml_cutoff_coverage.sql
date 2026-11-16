WITH bounds AS (
 SELECT DATE_ADD(DATE_TRUNC(DATE(MIN(purchase_at)),MONTH),INTERVAL 1 MONTH) AS lo,
 DATE_ADD(DATE_TRUNC(DATE(MAX(purchase_at)),MONTH),INTERVAL 1 MONTH) AS hi
 FROM {{ ref('int_ml_order_events') }}
), expected AS (
 SELECT TIMESTAMP(DATETIME(d),'America/Sao_Paulo') AS ts
 FROM bounds,UNNEST(GENERATE_DATE_ARRAY(lo,hi,INTERVAL 1 MONTH)) AS d
), actual AS (SELECT DISTINCT feature_timestamp AS ts FROM {{ ref('customer_features_monthly') }})
SELECT COALESCE(e.ts,a.ts) AS missing_cutoff FROM expected e FULL OUTER JOIN actual a USING(ts)
WHERE e.ts IS NULL OR a.ts IS NULL
