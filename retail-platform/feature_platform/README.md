# Customer and product feature platform

Both entity types passed the local historical/archive verification report on 16 November 2026. Current repository changes still need their own clean-environment integration run.

See [model and feature contracts](../docs/MODELS_AND_METRICS.md), [setup](../docs/SETUP.md), and [acceptance checks](../docs/NEXVIA_ACCEPTANCE.md).

Historical views use a 35-day TTL and are offline-only. Separate archive views have no online age limit solely to demonstrate the historical 2018 snapshots. They preserve original timestamps and are not fresh production features. Feature tables are unpartitioned and clustered by entity; sandbox whole-table expiration still applies.

The standalone verifier builds no warehouse tables: run the Dagster pipeline or dbt feature build first. It compares five examples per entity, tests before-first and before-cutoff requests, then validates materialized archive values and timestamps. Runtime evidence contains identifiers and remains local under ignored evidence directories.
