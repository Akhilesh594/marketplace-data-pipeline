from datetime import timedelta
import os
from feast import Entity, FeatureService, FeatureView, Field, ValueType
from feast.types import Float64, Int64
from feast.infra.offline_stores.bigquery_source import BigQuerySource

FIELDS = {"orders_30d":Int64,"orders_90d":Int64,"units_30d":Int64,"units_90d":Int64,"placed_item_value_90d_brl":Float64,"average_item_price_90d_brl":Float64,"days_since_last_order":Int64}
product = Entity(name="product",join_keys=["product_id"],value_type=ValueType.STRING)
source = BigQuerySource(name="olist_product_monthly_source",
    table=os.environ["GCP_PROJECT_ID"]+".olist_analytics.product_features_monthly",
    timestamp_field="feature_timestamp")
product_activity = FeatureView(
    name="product_activity",entities=[product],ttl=timedelta(days=35),
    schema=[Field(name=n,dtype=t) for n,t in FIELDS.items()],source=source,online=False,
    description="Historical monthly placed-order features; event-time approximation.")
product_activity_archive = FeatureView(
    name="product_activity_archive",entities=[product],ttl=timedelta(0),
    schema=[Field(name=n,dtype=t) for n,t in FIELDS.items()],source=source,online=True,
    description="ARCHIVE DEMO ONLY. No online age limit; original timestamps retained. Not for current predictions.")
product_activity_service = FeatureService(name="product_activity_service",features=[product_activity])
product_activity_archive_service = FeatureService(name="product_activity_archive_service",features=[product_activity_archive])
