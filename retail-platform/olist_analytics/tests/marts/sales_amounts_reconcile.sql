WITH source_totals AS (
    SELECT
        COALESCE(SUM(price), 0) AS price_total,
        COALESCE(SUM(freight_value), 0) AS freight_total,
        COALESCE(SUM(IF(o.order_status = 'delivered', i.price, 0)), 0)
            AS delivered_price_total
    FROM {{ ref('stg_order_items') }} AS i
    LEFT JOIN {{ ref('stg_orders') }} AS o ON i.order_id = o.order_id
),
fact_totals AS (
    SELECT
        COALESCE(SUM(item_price), 0) AS price_total,
        COALESCE(SUM(freight_value), 0) AS freight_total,
        COALESCE(SUM(IF(order_status = 'delivered', item_price, 0)), 0)
            AS delivered_price_total
    FROM {{ ref('fact_sales') }}
)
SELECT 'sales_totals_mismatch' AS issue
FROM source_totals AS s CROSS JOIN fact_totals AS f
WHERE s.price_total != f.price_total
   OR s.freight_total != f.freight_total
   OR s.delivered_price_total != f.delivered_price_total
