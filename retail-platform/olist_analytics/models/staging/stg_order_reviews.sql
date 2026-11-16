{{ config(materialized='view') }}

SELECT
    review_id,
    order_id,
    SAFE_CAST(review_score AS INT64) AS review_score,
    review_comment_title,
    review_comment_message,
    SAFE_CAST(review_creation_date AS DATETIME) AS review_created_at,
    SAFE_CAST(review_answer_timestamp AS DATETIME) AS review_answered_at
FROM {{ source('olist', 'order_reviews') }}
