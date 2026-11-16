WITH counts AS (
    SELECT 'fact_sales' AS model_name,
        (SELECT COUNT(*) FROM {{ ref('stg_order_items') }}) AS expected_rows,
        (SELECT COUNT(*) FROM {{ ref('fact_sales') }}) AS actual_rows
    UNION ALL
    SELECT 'dim_customer' AS model_name,
        (SELECT COUNT(*) FROM {{ ref('stg_customers') }}) AS expected_rows,
        (SELECT COUNT(*) FROM {{ ref('dim_customer') }}) AS actual_rows
    UNION ALL
    SELECT 'dim_product' AS model_name,
        (SELECT COUNT(*) FROM {{ ref('stg_products') }}) AS expected_rows,
        (SELECT COUNT(*) FROM {{ ref('dim_product') }}) AS actual_rows
    UNION ALL
    SELECT 'dim_store' AS model_name,
        (SELECT COUNT(*) FROM {{ ref('stg_sellers') }}) AS expected_rows,
        (SELECT COUNT(*) FROM {{ ref('dim_store') }}) AS actual_rows
)
SELECT * FROM counts WHERE actual_rows != expected_rows
