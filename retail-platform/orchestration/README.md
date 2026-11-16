# Five-stage orchestration

See [the setup guide](../docs/SETUP.md) for commands and credentials.
The active graph is airbyte_raw -> olist_staging -> olist_warehouse -> olist_history_metrics -> olist_ml_features.
Each stage verifies its outputs before downstream work. The feature stage builds/tests customer and product tables and verifies Feast historical/archive online retrieval.

The launcher keeps new schedules disabled by default and configures a single concurrent run. GET monitoring retries temporary failures; ambiguous job-creation POST failures are not retried automatically. An existing active job is attached to, and explicit --resume-job validates connection membership. Remote jobs may continue after local cancellation: inspect Airbyte before retrying.

The daily schedule is 09:00 Asia/Kolkata. This is a local dev deployment requiring running services, credentials, and internet. Old run snapshots can retain four assets; use the current job graph after reloading the code location.
