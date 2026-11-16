SELECT 'geolocation' AS table_name, 'geolocation_lat' AS column_name
FROM {{ source('olist', 'geolocation') }}
WHERE NULLIF(TRIM(geolocation_lat), '') IS NOT NULL
  AND SAFE_CAST(geolocation_lat AS FLOAT64) IS NULL
UNION ALL
SELECT 'geolocation' AS table_name, 'geolocation_lng' AS column_name
FROM {{ source('olist', 'geolocation') }}
WHERE NULLIF(TRIM(geolocation_lng), '') IS NOT NULL
  AND SAFE_CAST(geolocation_lng AS FLOAT64) IS NULL
UNION ALL
SELECT 'order_items' AS table_name, 'order_item_id' AS column_name
FROM {{ source('olist', 'order_items') }}
WHERE NULLIF(TRIM(order_item_id), '') IS NOT NULL
  AND SAFE_CAST(order_item_id AS INT64) IS NULL
UNION ALL
SELECT 'order_items' AS table_name, 'shipping_limit_date' AS column_name
FROM {{ source('olist', 'order_items') }}
WHERE NULLIF(TRIM(shipping_limit_date), '') IS NOT NULL
  AND SAFE_CAST(shipping_limit_date AS DATETIME) IS NULL
UNION ALL
SELECT 'order_items' AS table_name, 'price' AS column_name
FROM {{ source('olist', 'order_items') }}
WHERE NULLIF(TRIM(price), '') IS NOT NULL
  AND SAFE_CAST(price AS NUMERIC) IS NULL
UNION ALL
SELECT 'order_items' AS table_name, 'freight_value' AS column_name
FROM {{ source('olist', 'order_items') }}
WHERE NULLIF(TRIM(freight_value), '') IS NOT NULL
  AND SAFE_CAST(freight_value AS NUMERIC) IS NULL
UNION ALL
SELECT 'order_payments' AS table_name, 'payment_sequential' AS column_name
FROM {{ source('olist', 'order_payments') }}
WHERE NULLIF(TRIM(payment_sequential), '') IS NOT NULL
  AND SAFE_CAST(payment_sequential AS INT64) IS NULL
UNION ALL
SELECT 'order_payments' AS table_name, 'payment_installments' AS column_name
FROM {{ source('olist', 'order_payments') }}
WHERE NULLIF(TRIM(payment_installments), '') IS NOT NULL
  AND SAFE_CAST(payment_installments AS INT64) IS NULL
UNION ALL
SELECT 'order_payments' AS table_name, 'payment_value' AS column_name
FROM {{ source('olist', 'order_payments') }}
WHERE NULLIF(TRIM(payment_value), '') IS NOT NULL
  AND SAFE_CAST(payment_value AS NUMERIC) IS NULL
UNION ALL
SELECT 'order_reviews' AS table_name, 'review_score' AS column_name
FROM {{ source('olist', 'order_reviews') }}
WHERE NULLIF(TRIM(review_score), '') IS NOT NULL
  AND SAFE_CAST(review_score AS INT64) IS NULL
UNION ALL
SELECT 'order_reviews' AS table_name, 'review_creation_date' AS column_name
FROM {{ source('olist', 'order_reviews') }}
WHERE NULLIF(TRIM(review_creation_date), '') IS NOT NULL
  AND SAFE_CAST(review_creation_date AS DATETIME) IS NULL
UNION ALL
SELECT 'order_reviews' AS table_name, 'review_answer_timestamp' AS column_name
FROM {{ source('olist', 'order_reviews') }}
WHERE NULLIF(TRIM(review_answer_timestamp), '') IS NOT NULL
  AND SAFE_CAST(review_answer_timestamp AS DATETIME) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_name_lenght' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_name_lenght), '') IS NOT NULL
  AND SAFE_CAST(product_name_lenght AS INT64) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_description_lenght' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_description_lenght), '') IS NOT NULL
  AND SAFE_CAST(product_description_lenght AS INT64) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_photos_qty' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_photos_qty), '') IS NOT NULL
  AND SAFE_CAST(product_photos_qty AS INT64) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_weight_g' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_weight_g), '') IS NOT NULL
  AND SAFE_CAST(product_weight_g AS NUMERIC) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_length_cm' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_length_cm), '') IS NOT NULL
  AND SAFE_CAST(product_length_cm AS NUMERIC) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_height_cm' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_height_cm), '') IS NOT NULL
  AND SAFE_CAST(product_height_cm AS NUMERIC) IS NULL
UNION ALL
SELECT 'products' AS table_name, 'product_width_cm' AS column_name
FROM {{ source('olist', 'products') }}
WHERE NULLIF(TRIM(product_width_cm), '') IS NOT NULL
  AND SAFE_CAST(product_width_cm AS NUMERIC) IS NULL
