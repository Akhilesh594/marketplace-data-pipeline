from datetime import timedelta
import os
from feast import Entity, FeatureService, FeatureView, Field, ValueType
from feast.types import Float64, Int64
from feast.infra.offline_stores.bigquery_source import BigQuerySource

FIELDS = {"orders_lifetime":Int64,"orders_30d":Int64,"orders_90d":Int64,"placed_item_value_90d_brl":Float64,"average_order_value_90d_brl":Float64,"days_since_last_order":Int64,"customer_age_days":Int64}
customer = Entity(name="customer",join_keys=["customer_unique_id"],value_type=ValueType.STRING)
source = BigQuerySource(name="olist_customer_monthly_source",
    table=os.environ["GCP_PROJECT_ID"]+".olist_analytics.customer_features_monthly",
    timestamp_field="feature_timestamp")
customer_activity = FeatureView(
    name="customer_activity",entities=[customer],ttl=timedelta(days=35),
    schema=[Field(name=n,dtype=t) for n,t in FIELDS.items()],source=source,online=False,
    description="Historical monthly placed-order features; event-time approximation.")
customer_activity_archive = FeatureView(
    name="customer_activity_archive",entities=[customer],ttl=timedelta(0),
    schema=[Field(name=n,dtype=t) for n,t in FIELDS.items()],source=source,online=True,
    description="ARCHIVE DEMO ONLY. No online age limit; original timestamps retained. Not for current predictions.")
customer_activity_service = FeatureService(name="customer_activity_service",features=[customer_activity])
customer_activity_archive_service = FeatureService(name="customer_activity_archive_service",features=[customer_activity_archive])
