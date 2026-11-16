# Initial Olist star schema

- fact_sales: one row per order item. Orders with no items do not appear here; use stg_orders for order-level counts.
- dim_customer: one row per source customer_id. Use customer_unique_id to count people and repeat purchases. Source customer_id is order-associated. This is not yet an SCD Type 2 dimension.
- dim_product: product details; missing translations fall back to original names.
- dim_store: seller is the store equivalent; no physical stores are claimed.
- dim_date: one row per calendar day over order purchase dates. Datetimes retain source local wall-clock values, without assuming UTC.

Prices are in dataset currency (BRL). item_price excludes freight. All order statuses are preserved. A delivered-only sales measure must filter order_status='delivered'. Do not claim actual profit or margin: no cost source is present.

Payments and reviews are not joined to the fact, avoiding order-level one-to-many multiplication. There are no synthetic retail records in these models.

Builds replace these five derived tables. Raw tables, staging models and credentials are not modified. Tests validate keys, references, grain, row counts and sales totals. Source data quality is tested in the staging batch.
