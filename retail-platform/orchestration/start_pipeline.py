"""Start Dagster locally. Credentials are prompted privately, not stored in files."""
import argparse
import json
from getpass import getpass
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--resume-job", type=int, help="Resume one existing Airbyte sync without creating a new job")
    args = parser.parse_args()
    if not os.getenv("AIRBYTE_CONNECTION_ID"):
        os.environ["AIRBYTE_CONNECTION_ID"] = input("Airbyte connection ID: ").strip()
    if not os.environ["AIRBYTE_CONNECTION_ID"]:
        raise RuntimeError("AIRBYTE_CONNECTION_ID is required.")
    os.environ.setdefault("AIRBYTE_URL", "http://localhost:8000")
    for name, label in [
        ("AIRBYTE_CLIENT_ID", "Airbyte application Client-ID"),
        ("AIRBYTE_CLIENT_SECRET", "Airbyte application Client-Secret"),
    ]:
        if not os.getenv(name):
            os.environ[name] = getpass(label + " (input hidden): ").strip()
    from airbyte_client import AirbyteClient
    client = AirbyteClient()
    client.get_connection()
    print("Airbyte API authentication and connection lookup passed. No sync started.")
    resume = None
    if args.resume_job is not None:
        resume = client.resume_job(args.resume_job)
        print("Resume target: job " + str(args.resume_job) + "; status=" + str(resume["status"]))
    if args.check_only:
        return
    home = HERE / ".dagster_home"
    home.mkdir(exist_ok=True)
    config = home / "dagster.yaml"
    if not config.exists():
        config.write_text(
            "telemetry:\n  enabled: false\nrun_coordinator:\n"
            "  module: dagster.core.run_coordinator\n  class: QueuedRunCoordinator\n"
            "  config:\n    max_concurrent_runs: 1\n", encoding="utf-8")
    if resume is not None:
        marker = home / "resume_airbyte_job.json"
        value = {"job_id": args.resume_job}
        if marker.exists():
            if json.loads(marker.read_text(encoding="utf-8")) != value:
                raise RuntimeError("A different resume request already exists; inspect it before continuing.")
        else:
            with marker.open("x", encoding="utf-8") as output:
                json.dump(value, output)
        print("The next ingestion asset will resume this job once; no new sync will be submitted.")
    os.environ["DAGSTER_HOME"] = str(home)
    os.environ["DBT_ENGINE_MANAGE_STATE"] = "false"
    dagster = Path(sys.executable).parent / ("dagster.exe" if os.name == "nt" else "dagster")
    if not dagster.is_file():
        raise SystemExit("Run with .venv-dagster/Scripts/python.exe")
    print("Open http://127.0.0.1:3000 ; choose Jobs > retail_pipeline > Materialize all.")
    print("Launching a run starts an Airbyte full refresh and rebuilds derived tables.")
    print("The daily 09:00 India schedule is defined but OFF by default.")
    try:
        raise SystemExit(subprocess.call([
            str(dagster), "dev", "-f", str(HERE / "definitions.py"),
            "--host", "127.0.0.1", "--port", "3000",
        ], cwd=HERE, env=os.environ.copy()))
    finally:
        for key in ("AIRBYTE_CLIENT_SECRET", "AIRBYTE_CLIENT_ID"):
            os.environ.pop(key, None)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        raise SystemExit(1)
