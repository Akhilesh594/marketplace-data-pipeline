# Nexvia DE-04 acceptance checklist

Based on the brief supplied in the project conversation. Deadline: 30 November 2026. This checklist does not assert that a public cloud URL was an explicit requirement; confirm the submission portal's current instructions.

| Deliverable | Current evidence | Remaining work |
|---|---|---|
| PostgreSQL source and Airbyte ingestion | Nine source tables and successful historical load | Reproduce from external Kaggle files on a clean machine |
| Retail star schema | Fact and customer/product/store/date dimensions; SQL tests | Generate/review dbt model documentation |
| Type 2 customer history | Versioned location observations with validity tests | Explain observation-based limits |
| Dagster assets and schedule | Five-stage definition; integrated success reported by author | Capture successful unattended scheduled tick/run |
| Revenue/margin/repeat metrics | Shared SQL measures and reconciliation | Margin blocked by missing cost data; formal semantic-engine acceptance needs clarification |
| Feast customer/product offline and online | Both entities passed local verification on 16 November 2026 | Archive demo is not fresh production feature serving |
| Metabase dashboards | Two dashboards and ten custom questions | Add sanitized rendering evidence/demo recording |
| Public GitHub and setup | Current source/docs publication | Verify clean-clone setup; keep commits and CI evidence |
| Architecture, data, and SDK/API docs | README diagram, model/metric contracts, setup guide | Expand individual column dictionary if required |
| Tests and performance | SQL tests, 13 mocked client tests, six feature comparison tests, local verification | Record reproducible timings; no untrained-model accuracy claims |
| Ten-minute presentation | Demo outline included | Record/present the demonstration |
| Individual reflection | Not written on behalf of the author | Author describes own contribution, decisions, and learning |
| Cloud hosting | Not provisioned | Optional delivery choice unless assessor explicitly requires it |

The earlier progress document is superseded by this evidence-based checklist. Product features and five-stage integration were subsequently added; they are no longer merely planned. An installed script, a successful component check, a reported integration run, and an unattended hosted run are different kinds of evidence.
