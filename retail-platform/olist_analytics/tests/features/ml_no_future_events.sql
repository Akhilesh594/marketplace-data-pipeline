SELECT * FROM {{ ref('customer_features_monthly') }}
WHERE first_purchase_at IS NULL OR last_purchase_at IS NULL
   OR first_purchase_at >= cutoff_local OR last_purchase_at >= cutoff_local
   OR feature_timestamp != TIMESTAMP(cutoff_local, 'America/Sao_Paulo')
