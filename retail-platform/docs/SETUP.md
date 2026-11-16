# Reproduce the local demonstration

This guide targets Windows PowerShell and Python 3.11, matching the demonstrated environment. Runtime paths also accommodate standard Linux virtual environments, but a Linux integration run has not been verified.

## Prerequisites

- Git, Python 3.11, Docker Desktop with Linux containers/WSL2, and enough resources for Airbyte.
- Google Cloud project with BigQuery available, US datasets `olist_raw`, `olist_analytics`, and `olist_feast_work`.
- A Google service account allowed to run BigQuery jobs and read/write only the required datasets. Keep its JSON key outside this checkout. Never commit it.
- Kaggle Olist CSV files, downloaded separately.

Clone the repository and change into `retail-platform`. Run `scripts/setup-environments.ps1`. Top-level dependencies are pinned in `requirements-dbt.txt`, `orchestration/requirements.txt`, and `requirements-feast.txt`. Transitive dependencies are not a full lockfile; run `pip check` in every environment.

## Source PostgreSQL and Airbyte

On the existing machine, use the existing PostgreSQL Docker container and data volume; do not replace or delete them. On a fresh machine, create PostgreSQL 17 with persistent storage and a private password, then create database `retail_source` and schema `raw`.

Import the CSV headers as column names, initially using text columns. Map these files to `raw` tables:

| Kaggle CSV | PostgreSQL table |
|---|---|
| olist_orders_dataset.csv | orders |
| olist_customers_dataset.csv | customers |
| olist_order_items_dataset.csv | order_items |
| olist_order_payments_dataset.csv | order_payments |
| olist_order_reviews_dataset.csv | order_reviews |
| olist_products_dataset.csv | products |
| olist_sellers_dataset.csv | sellers |
| olist_geolocation_dataset.csv | geolocation |
| product_category_name_translation.csv | category_translation |

Use PostgreSQL `COPY ... FROM ... WITH (FORMAT csv, HEADER true)` or pgAdmin's CSV import after creating each table with the file's header columns. Preserve quoted multiline review text and leading zeros. Loading source CSVs is a prerequisite, not part of the scheduled Dagster job. Compare source counts with the original files before ingestion.

Install Airbyte using its [official abctl quickstart](https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart). Configure PostgreSQL source on `host.docker.internal:5432` when connecting from Airbyte's local Docker environment. Configure a BigQuery destination in `olist_raw`, US. Select all nine tables, Full Refresh/Overwrite, destination-defined namespace, and Manual scheduling. Record the connection ID and generate Airbyte application credentials. Do not export a secret-bearing connector configuration into Git.

## Configure this checkout

In PowerShell, set these process variables using your own values:

```powershell
$env:GCP_PROJECT_ID = 'your-project-id'
$env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\private\service-account.json'
$env:DBT_PROFILES_DIR = (Resolve-Path '.\config').Path
$env:AIRBYTE_CONNECTION_ID = 'your-connection-id'
$env:AIRBYTE_URL = 'http://localhost:8000'
Copy-Item '.\config\profiles.example.yml' '.\config\profiles.yml'
```

`profiles.yml` is ignored. `.env.example` documents variables; no automatic `.env` loader is installed. The Dagster launcher privately prompts for application Client-ID and Client-Secret if missing. These are not your Airbyte web login password.

## Verify and run

Run the mocked tests with `PYTHONPATH` set so local modules are importable:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\orchestration').Path
.\.venv-dagster\Scripts\python.exe -m unittest discover -s orchestration\tests -v
$env:PYTHONPATH = (Resolve-Path '.\feature_platform').Path
.\.venv-feast\Scripts\python.exe -m unittest discover -s feature_platform\tests -v
Remove-Item Env:PYTHONPATH
.\.venv-dagster\Scripts\python.exe orchestration\validate_definitions.py
.\.venv-dagster\Scripts\python.exe orchestration\start_pipeline.py --check-only
.\.venv-dagster\Scripts\python.exe orchestration\start_pipeline.py
```

The launcher creates local Dagster storage, obtains credentials, and opens a dev deployment at `http://127.0.0.1:3000`. It does not launch ingestion merely by starting. Select Jobs > retail_pipeline > Materialize all to request a Full Refresh/Overwrite and downstream rebuilds. Avoid simultaneous manual edits to the same destination tables.

The five stages run in order: ingestion, staging, warehouse, history/metrics, ML features/Feast. The last step executes three feature models and thirteen SQL tests, then historical and archive online checks. Reports remain under ignored `evidence/` directories.

For a standalone feature verification after the upstream tables exist:

```powershell
.\.venv-feast\Scripts\python.exe feature_platform\run_feast_demo.py
```

The daily schedule is 09:00 Asia/Kolkata and starts disabled in a new deployment. Enable it only when the local services can remain running. Keep one active pipeline run at a time. Runtime credentials must exist in the Dagster process environment.

## Metabase

Use the existing Metabase installation at `http://localhost:3001`. A fresh installation must persist its application database and map host port 3001 to container port 3000. Connect BigQuery with the configured project and dataset `olist_analytics`. The Metabase connection ID can differ between installations.

Review dashboard SQL without changing Metabase:

```powershell
.\.venv\Scripts\python.exe scripts\build_olist_dashboards.py --plan
```

Create/reconcile the two dashboards, using your actual connection ID:

```powershell
.\.venv\Scripts\python.exe scripts\build_olist_dashboards.py --database-id 2
```

The builder prompts for Metabase credentials, preserves existing cards, and saves local dashboard links. Questions use the selected project's warehouse. Inspect all charts after creation. This integration targets the demonstrated Metabase v0.65 API; other releases require verification.
