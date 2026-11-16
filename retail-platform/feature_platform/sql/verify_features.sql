-- Current feature coverage and earliest preserved historical cutoffs.
SELECT 'customer' AS entity,COUNT(*) AS feature_rows,
 COUNT(DISTINCT customer_unique_id) AS entities,
 COUNT(DISTINCT cutoff_local) AS monthly_cutoffs,
 MIN(cutoff_local) AS earliest_cutoff,MAX(cutoff_local) AS latest_cutoff
FROM `YOUR_GCP_PROJECT_ID.olist_analytics.customer_features_monthly`
UNION ALL
SELECT 'product',COUNT(*),COUNT(DISTINCT product_id),COUNT(DISTINCT cutoff_local),
 MIN(cutoff_local),MAX(cutoff_local)
FROM `YOUR_GCP_PROJECT_ID.olist_analytics.product_features_monthly`;

-- Expected: no rows; neither feature table has partitioning columns.
SELECT table_name,column_name FROM `YOUR_GCP_PROJECT_ID.olist_analytics.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('customer_features_monthly','product_features_monthly')
 AND is_partitioning_column='YES';
