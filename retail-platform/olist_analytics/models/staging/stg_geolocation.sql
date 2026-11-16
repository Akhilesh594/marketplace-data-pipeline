{{ config(materialized='view') }}

SELECT
    geolocation_zip_code_prefix,
    SAFE_CAST(geolocation_lat AS FLOAT64) AS latitude,
    SAFE_CAST(geolocation_lng AS FLOAT64) AS longitude,
    LOWER(TRIM(geolocation_city)) AS city,
    UPPER(TRIM(geolocation_state)) AS state
FROM {{ source('olist', 'geolocation') }}
