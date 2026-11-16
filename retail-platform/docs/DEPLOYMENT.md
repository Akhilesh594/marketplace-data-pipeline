# Free-first deployment decision

Reviewed against provider documentation on 16 November 2026. No paid resources have been provisioned. GitHub publication is not deployment of the running data stack.

## Recommended internship demonstration

| Component | Location | Limitation |
|---|---|---|
| Code and setup | Public GitHub repository | Repository stores source, not running databases/services |
| PostgreSQL, Airbyte, Dagster | Existing laptop/Docker | Laptop must remain available for execution |
| BigQuery | Existing Google Cloud sandbox | Quotas and automatic expiration apply; preserve source/rebuild code |
| Feast registry and SQLite online store | Existing laptop | Archive demonstration with persistent local state |
| Metabase | Existing laptop | Local viewing while service runs |
| Optional project landing page | Static hosting such as Vercel | Describes the project; does not host the pipeline |
| Demo recording | Shareable video | Shows results without exposing service ports or credentials |

This avoids a recurring hosting bill while retaining the implemented tools. Local compute/electricity and internet are still required. A public URL independent of the laptop requires a separate hosting arrangement; no such deployment is claimed.

## Why Vercel and Render do not host this whole stack for free

Vercel Functions are request-driven and subject to execution-duration limits. They are not an always-running Dagster daemon, PostgreSQL server, Metabase JVM, or Airbyte Kubernetes deployment. A static project page can be hosted there. A browser page's `localhost` link refers to the viewer's own machine, so it cannot connect a remote reviewer to your laptop services.

Render Free web services spin down after 15 minutes without inbound traffic and have an ephemeral filesystem. SQLite/registry files and other local changes can disappear on restart, redeploy, or spin-down. Persistent disks require a paid service. Free Postgres is limited to 1 GB and expires after 30 days; it is not durable long-term project storage. A short-lived stateless demonstration is a different architecture from the working stack.

Airbyte abctl manages a Docker-based Kubernetes installation with multiple components. It cannot be reduced to a single free Render web service by uploading this repository. Metabase also needs sufficient JVM resources and a durable application database; free hosting here has not been verified.

## Later always-on deployment

With a budget, evaluate a suitably sized cloud VM or managed services. Migrate PostgreSQL data and configure a dedicated ingestion account; change laptop-specific hostnames to reachable private endpoints. Deploy Airbyte with its supported deployment method. Run Dagster webserver, daemon, and code location with persistent metadata and restart policies. Move Metabase application data from H2 to PostgreSQL before production use. Persist Feast state or select a suitable shared online store. Keep admin interfaces/private database ports restricted; publish authenticated HTTPS dashboard access.

Acceptance: run successfully with the laptop switched off; verify scheduled execution, source/warehouse counts, feature tests, stored state after restart, and dashboard rendering. An unattended scheduled cloud run has not been demonstrated.

## References

- [Render free services](https://render.com/docs/free)
- [Render persistent disks](https://render.com/docs/disks)
- [Vercel Function limits](https://vercel.com/docs/functions/limitations)
- [Airbyte quickstart](https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart)
- [BigQuery sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)
- [Metabase application database migration](https://www.metabase.com/docs/latest/installation-and-operation/migrating-from-h2)
