{{ config(materialized='table') }}

WITH boundaries AS (
    SELECT
        MIN(DATE(order_purchase_at)) AS first_date,
        MAX(DATE(order_purchase_at)) AS last_date
    FROM {{ ref('stg_orders') }}
),
calendar AS (
    SELECT calendar_date
    FROM boundaries,
    UNNEST(GENERATE_DATE_ARRAY(first_date, last_date)) AS calendar_date
)
SELECT
    CAST(FORMAT_DATE('%Y%m%d', calendar_date) AS INT64) AS date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date) AS year,
    EXTRACT(QUARTER FROM calendar_date) AS quarter,
    EXTRACT(MONTH FROM calendar_date) AS month,
    FORMAT_DATE('%B', calendar_date) AS month_name,
    EXTRACT(ISOWEEK FROM calendar_date) AS iso_week,
    EXTRACT(DAY FROM calendar_date) AS day_of_month,
    FORMAT_DATE('%A', calendar_date) AS day_name,
    EXTRACT(DAYOFWEEK FROM calendar_date) IN (1, 7) AS is_weekend
FROM calendar
