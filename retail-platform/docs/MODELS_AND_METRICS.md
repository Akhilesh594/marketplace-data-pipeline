# Model, metric, and feature contracts

## Warehouse relationships

`fact_sales` has grain `(order_id, order_item_id)` and a hashed sale key. It links to `dim_customer` through the order-associated customer ID, `dim_product` through product ID, `dim_store` through seller ID, and `dim_date` through purchase date. Sellers represent stores in this project. Do not join raw payment/review rows directly into an item fact and then sum prices; multiple matches can inflate totals.

`customer_unique_id` is the stable buyer identifier. `customer_id` is associated with an order/customer observation. Customer history deduplicates purchase-time observations, retains changes in location attributes, and uses start-inclusive/end-exclusive validity intervals. `fact_sales_history` temporally matches those versions. This is observed history, not audited CDC.

## Business measures

| Measure | Definition | Scope |
|---|---|---|
| Delivered item sales, BRL | Sum of item price | Delivered orders; excludes freight, costs, and refund accounting |
| Delivered orders | Distinct order ID | Delivered item-bearing orders |
| AOV | Delivered item sales / delivered orders | BRL; safe division |
| Repeat buyer rate | Buyers with >=2 delivered orders / buyers with >=1 delivered order | Full loaded period; dashboard scales to percent |
| Monthly sales/orders | Group delivered measures by purchase month | Not delivery month |
| Order status distribution | Count staging orders by status | Includes all source orders, including orders without items |
| Margin | NULL plus explanatory note | Product costs absent; unsupported |

Shared SQL metric tables centralize these calculations. A formal semantic-layer engine has not been deployed. Dashboard v1 has no date filters; do not present full-period repeat rate as a rolling-period retention metric.

## Monthly ML feature contracts

Grains: `(customer_unique_id, feature_timestamp)` and `(product_id, feature_timestamp)`. Cutoffs are first-of-month boundaries from the month after the earliest source purchase through the month after the latest. Windows include the lower bound and exclude the cutoff. Only entities with prior item-bearing placed orders are represented.

Customer fields: `orders_lifetime`, `orders_30d`, `orders_90d`, `placed_item_value_90d_brl`, `average_order_value_90d_brl`, `days_since_last_order`, `customer_age_days`.

Product fields are defined in `feature_platform/feature_repo/product_features.py`; they represent 30/90-day order counts and units, 90-day placed item value/average item price, and days since last order. Units count order-item rows. Neither feature set filters on final delivery status or uses later reviews/delivery outcomes.

Source timestamps are naive; America/Sao_Paulo is the explicit interpretation. Purchase-time availability of order/item attributes is assumed because per-field audit timestamps are absent. Source corrections may change reconstructed history.

## Retrieval example

Run with the Feast environment and configured `GCP_PROJECT_ID`/credentials:

```python
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path="feature_platform/feature_repo")
service = store.get_feature_service("customer_activity_service")
entities = pd.DataFrame({
    "customer_unique_id": ["replace-with-an-existing-source-id"],
    "event_timestamp": pd.to_datetime(["2018-09-01T03:00:00Z"]),
})
historical = store.get_historical_features(entity_df=entities, features=service).to_df()
```

For online demonstration, use `customer_activity_archive_service` or `product_activity_archive_service` after materialization. Archive views retain original timestamps and disable the online age limit solely for historical demonstration. No current prediction endpoint or model accuracy is claimed.

## Validation

SQL checks cover source validity, grains, domains, reconciliation, future-event exclusion, non-empty features, and complete cutoff coverage. Feast verification compares five examples per entity against BigQuery, checks requests before the first snapshot and immediately before a later cutoff, and compares archive online values/timestamps. These sampled checks complement SQL tests; they are not a full production correctness or performance certification.
