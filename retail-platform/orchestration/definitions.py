"""Five dependent asset bundles, from ingestion to verified Feast features."""
import json
import os
from pathlib import Path
import shutil
import subprocess

from dagster import (
    asset, AssetSelection, Definitions, Failure, MaterializeResult,
    ScheduleDefinition, DefaultScheduleStatus, define_asset_job, in_process_executor,
)
from airbyte_client import AirbyteClient, CONNECTION_ID

ROOT = Path(__file__).resolve().parents[1]
DBT_PROJECT = ROOT / "olist_analytics"
DBT = ROOT / ".venv" / ("Scripts/dbt.exe" if os.name == "nt" else "bin/dbt")
GROUP = "retail_pipeline"

def run_dbt(context, phase, selectors):
    if not DBT.is_file():
        raise Failure("Project dbt executable is missing: " + str(DBT))
    environment = os.environ.copy()
    environment["DBT_ENGINE_MANAGE_STATE"] = "false"
    command = [str(DBT), "--no-use-colors", "build", "--project-dir", str(DBT_PROJECT),
               "--select", *selectors]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                               errors="replace", env=environment)
    try:
        for line in process.stdout:
            context.log.info(line.rstrip())
        code = process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=30)
    artifact = DBT_PROJECT / "target" / "run_results.json"
    metadata = {"phase": phase}
    if artifact.is_file():
        evidence = ROOT / "orchestration" / "evidence" / context.run_id
        evidence.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, evidence / (phase + "_run_results.json"))
    if code != 0:
        raise Failure("dbt " + phase + " failed. Inspect this step's logs. Downstream assets are blocked.")
    if not artifact.is_file():
        raise Failure("dbt returned success without run_results.json; cannot verify build.")
    results = json.loads(artifact.read_text(encoding="utf-8")).get("results", [])
    if not results:
        raise Failure("No dbt resources executed; check model/test selectors.")
    bad = [r for r in results if r.get("status") not in {"pass", "success", "warn"}]
    if bad:
        raise Failure("dbt results include unsuccessful resources; downstream assets blocked.")
    metadata["resources_executed"] = len(results)
    metadata["warning_count"] = sum(r.get("status") == "warn" for r in results)
    return MaterializeResult(metadata=metadata)

@asset(group_name=GROUP, description="Sync all nine PostgreSQL tables to BigQuery through Airbyte; wait for success.")
def airbyte_raw(context):
    client = AirbyteClient()
    client.log = context.log.warning
    client.get_connection()
    marker = ROOT / "orchestration" / ".dagster_home" / "resume_airbyte_job.json"
    claimed = marker.with_name("resume_claimed_" + context.run_id + ".json")
    try:
        marker.rename(claimed)
    except FileNotFoundError:
        job, attached = client.start_or_attach()
    else:
        resume_id = json.loads(claimed.read_text(encoding="utf-8"))["job_id"]
        job = client.resume_job(resume_id)
        attached = True
        context.log.info("Resuming monitoring of explicitly selected Airbyte job " + str(resume_id))
    job_id = job["jobId"]
    context.log.info(("Attached to existing" if attached else "Started") + " Airbyte job " + str(job_id))
    result = client.wait_for_success(job_id, log=context.log.info,
        timeout_seconds=int(os.getenv("AIRBYTE_WAIT_SECONDS", "3600")))
    return MaterializeResult(metadata={
        "job_id": str(job_id), "connection_id": CONNECTION_ID,
        "status": result["status"], "attached_to_existing_job": attached,
    })

@asset(group_name=GROUP, deps=[airbyte_raw], description="Build and test all nine staging views.")
def olist_staging(context):
    return run_dbt(context, "staging", ["path:models/staging", "path:tests/staging"])

@asset(group_name=GROUP, deps=[olist_staging], description="Build and test fact_sales and four dimensions.")
def olist_warehouse(context):
    return run_dbt(context, "warehouse", ["path:models/marts", "path:tests/marts"])

@asset(group_name=GROUP, deps=[olist_warehouse], description="Build/test observation-based customer history and shared metrics.")
def olist_history_metrics(context):
    return run_dbt(context, "history_metrics", [
        "path:models/history", "path:models/metrics", "path:tests/history", "path:tests/metrics",
    ])


@asset(group_name=GROUP, deps=[olist_history_metrics],
       description="Build/test customer/product features and verify historical/archive online Feast retrieval.")
def olist_ml_features(context):
    run_dbt(context, "ml_features", ["path:models/features", "path:tests/features"])
    python = ROOT / ".venv-feast" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise Failure("Feast environment missing; run the feature setup first.")
    environment = os.environ.copy()
    if not environment.get("GOOGLE_APPLICATION_CREDENTIALS"):
        raise Failure("Set GOOGLE_APPLICATION_CREDENTIALS before starting Dagster.")
    process = subprocess.Popen([str(python), "-u", str(ROOT / "feature_platform" / "run_feast_demo.py")],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace")
    try:
        for line in process.stdout:
            context.log.info(line.rstrip())
        code = process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=30)
    if code != 0:
        raise Failure("Feast verification failed. Review this step's logs.")
    path = ROOT / "feature_platform" / "evidence" / "feature_platform_verification.json"
    if not path.is_file():
        raise Failure("Feast returned without verification evidence.")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") != "passed" or any(
        report.get("entities", {}).get(name, {}).get("status") != "passed"
        for name in ("customer", "product")
    ):
        raise Failure("Customer/product Feast evidence is incomplete.")
    evidence = ROOT / "orchestration" / "evidence" / context.run_id
    evidence.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, evidence / path.name)
    return MaterializeResult(metadata={"phase":"ml_features", "entities":"customer, product",
        "mode":"historical_archive_demo", "verification_report":str(evidence / path.name)})

pipeline_job = define_asset_job(
    "retail_pipeline", selection=AssetSelection.groups(GROUP),
    executor_def=in_process_executor,
)
daily_schedule = ScheduleDefinition(
    name="retail_daily_9am_ist", job=pipeline_job,
    cron_schedule="0 9 * * *", execution_timezone="Asia/Kolkata",
    default_status=DefaultScheduleStatus.STOPPED,
)
defs = Definitions(
    assets=[airbyte_raw, olist_staging, olist_warehouse, olist_history_metrics, olist_ml_features],
    jobs=[pipeline_job], schedules=[daily_schedule],
)
