# Ten-minute demonstration

Before presenting: start existing services, confirm dashboard rendering, inspect a successful Dagster run, and retain local verification evidence. Avoid launching a full refresh during a timed presentation. Hide credentials and account panels while recording.

| Minutes | Screen | Explain |
|---|---|---|
| 0-1 | Architecture and source table list | Kaggle historical Olist data, nine tables, PostgreSQL source |
| 1-2 | Airbyte connection/history | Full Refresh/Overwrite batch ingestion into BigQuery |
| 2-4 | BigQuery SQL/models | Item-level grain, dimensions, observed Type 2 history, tested metrics |
| 4-6 | Metabase dashboards | Show actual results and discuss two defensible insights |
| 6-8 | Feature counts and verification summary | Monthly cutoffs, seven features each, historical vs archive online retrieval |
| 8-10 | Dagster current graph and successful run | Five dependencies, failure gates, schedule, limitations and next steps |

Suggested opening: "I built a retail analytics warehouse extended with a verified feature platform. PostgreSQL represents the source, Airbyte ingests it into BigQuery, dbt creates tested models, Dagster coordinates execution, Metabase explains business results, and Feast retrieves historical customer and product features."

Use BigQuery for live SQL validation, Metabase for business charts, and Dagster for execution evidence. Do not call the pipeline real-time, call gross item sales profit, or imply a prediction model has been trained. A hosted project description is not a remotely running pipeline.

For a free submission, share the GitHub folder and a short recording alongside the setup guide. Keep raw identifiers and service-account material outside the recording/repository.
