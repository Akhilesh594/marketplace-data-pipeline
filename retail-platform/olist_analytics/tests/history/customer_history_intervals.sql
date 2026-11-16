WITH intervals AS (
    SELECT *,
        LAG(valid_to) OVER (
            PARTITION BY customer_unique_id ORDER BY valid_from
        ) AS previous_valid_to
    FROM {{ ref('dim_customer_history') }}
)
SELECT customer_version_key
FROM intervals
WHERE (valid_to IS NOT NULL AND valid_to <= valid_from)
   OR previous_valid_to > valid_from
