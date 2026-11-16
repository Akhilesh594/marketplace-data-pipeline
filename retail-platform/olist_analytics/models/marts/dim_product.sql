{{ config(materialized='table') }}

SELECT
    p.product_id AS product_key,
    p.product_id,
    p.product_category_name AS category_name_original,
    COALESCE(t.product_category_name_english,
             p.product_category_name, 'unknown') AS category_name,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    p.product_photos_qty
FROM {{ ref('stg_products') }} AS p
LEFT JOIN {{ ref('stg_category_translation') }} AS t
  ON p.product_category_name = t.product_category_name
