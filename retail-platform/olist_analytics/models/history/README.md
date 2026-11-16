# Customer history and reusable metric tables

## History
dim_customer_history is observation-based Type 2 modelling. The stable person identifier is customer_unique_id. The source customer_id is associated with individual orders and is not a stable person identifier.
Location versions start at an order purchase datetime when a different location is observed; consecutive identical locations collapse into one version. valid_to is exclusive. One current version has a NULL valid_to.
These timestamps are observed purchase times, not verified move dates or a record of source-system updates. Same-time conflicting profiles use a deterministic customer_id tie-break and are surfaced by a warning test. No synthetic customer changes are inserted.
fact_sales_history adds the version key through a time-valid join; original fact_sales and dim_customer are preserved. Tests check no sales rows or amounts multiply or disappear.

## Shared metric definitions
Eligible sales: order_status = 'delivered'. Revenue is the dataset's gross delivered item sales value in BRL, excluding freight. It is a project revenue proxy, not Olist's recognised marketplace revenue.
Order count: distinct eligible order IDs represented in item data.
AOV: eligible item sales value divided by eligible order count.
Repeat customer rate: eligible people with at least two distinct eligible orders divided by all eligible people. Period is the full imported dataset history. Person ID is customer_unique_id.
Daily customer counts must not be summed to obtain unique customers over a longer period.
Margin is unavailable without product costs; margin_brl is NULL with an explicit note. Do not interpret NULL as zero.
metrics_customer_summary uses full history and must not be used directly as historical training features. Point-in-time features will be built separately for Feast.
These SQL metric tables are the reusable computation layer. A formal semantic-layer integration is still pending.
