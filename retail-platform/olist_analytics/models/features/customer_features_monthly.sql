{{ config(materialized='table', cluster_by=['customer_unique_id']) }}
-- Monthly snapshots for customers with at least one prior item-bearing placed order.
-- Monetary values are order item totals, excluding freight. Cancelled orders are not
-- retrospectively removed. Source timestamps are naive; Sao Paulo is an explicit
-- demonstration assumption, not verified source metadata.
WITH bounds AS (
    SELECT DATE_ADD(DATE_TRUNC(DATE(MIN(purchase_at)), MONTH), INTERVAL 1 MONTH) AS first_cutoff,
           DATE_ADD(DATE_TRUNC(DATE(MAX(purchase_at)), MONTH), INTERVAL 1 MONTH) AS last_cutoff
    FROM {{ ref('int_ml_order_events') }}
), cutoffs AS (
    SELECT DATETIME(cutoff_date) AS cutoff_at
    FROM bounds, UNNEST(GENERATE_DATE_ARRAY(first_cutoff, last_cutoff, INTERVAL 1 MONTH)) AS cutoff_date
), aggregated AS (
    SELECT e.customer_unique_id, c.cutoff_at,
        COUNT(*) AS orders_lifetime,
        COUNTIF(e.purchase_at >= DATETIME_SUB(c.cutoff_at, INTERVAL 30 DAY)) AS orders_30d,
        COUNTIF(e.purchase_at >= DATETIME_SUB(c.cutoff_at, INTERVAL 90 DAY)) AS orders_90d,
        SUM(IF(e.purchase_at >= DATETIME_SUB(c.cutoff_at, INTERVAL 90 DAY), e.placed_item_value_brl, 0)) AS placed_item_value_90d_brl,
        MIN(e.purchase_at) AS first_purchase_at,
        MAX(e.purchase_at) AS last_purchase_at
    FROM cutoffs c JOIN {{ ref('int_ml_order_events') }} e ON e.purchase_at < c.cutoff_at
    GROUP BY e.customer_unique_id, c.cutoff_at
)
SELECT customer_unique_id,
    TIMESTAMP(cutoff_at, 'America/Sao_Paulo') AS feature_timestamp,
    cutoff_at AS cutoff_local,
    orders_lifetime, orders_30d, orders_90d,
    CAST(placed_item_value_90d_brl AS FLOAT64) AS placed_item_value_90d_brl,
    CAST(COALESCE(SAFE_DIVIDE(placed_item_value_90d_brl, orders_90d), 0) AS FLOAT64) AS average_order_value_90d_brl,
    DATETIME_DIFF(cutoff_at, last_purchase_at, DAY) AS days_since_last_order,
    DATETIME_DIFF(cutoff_at, first_purchase_at, DAY) AS customer_age_days,
    first_purchase_at, last_purchase_at,
    'America/Sao_Paulo (assumed)' AS source_timezone_assumption
FROM aggregated
