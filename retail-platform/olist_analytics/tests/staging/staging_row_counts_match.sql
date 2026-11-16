SELECT 'orders' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'orders') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_orders') }})
UNION ALL
SELECT 'customers' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'customers') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_customers') }})
UNION ALL
SELECT 'geolocation' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'geolocation') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_geolocation') }})
UNION ALL
SELECT 'order_items' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'order_items') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_order_items') }})
UNION ALL
SELECT 'order_payments' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'order_payments') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_order_payments') }})
UNION ALL
SELECT 'order_reviews' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'order_reviews') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_order_reviews') }})
UNION ALL
SELECT 'products' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'products') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_products') }})
UNION ALL
SELECT 'sellers' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'sellers') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_sellers') }})
UNION ALL
SELECT 'category_translation' AS table_name
FROM (SELECT 1) AS count_anchor
WHERE (SELECT COUNT(*) FROM {{ source('olist', 'category_translation') }})
   != (SELECT COUNT(*) FROM {{ ref('stg_category_translation') }})
