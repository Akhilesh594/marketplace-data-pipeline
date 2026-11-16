"""Offline check of tracked publication files; never reads keys outside this repo."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    paths = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "."],
        cwd=ROOT,
    ).decode().split("\0")
    errors = []
    for name in filter(None, paths):
        path = ROOT / name
        if not path.is_file():
            continue
        parts = set(path.relative_to(ROOT).parts)
        if parts & {"evidence", "data", "target", "logs", ".dagster_home", "secrets"}:
            errors.append(name + ": generated/private runtime directory")
        if path.suffix.lower() in {".csv", ".parquet", ".db", ".sqlite", ".pem", ".key"}:
            errors.append(name + ": data/key/runtime file")
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            errors.append(name + ": environment secrets file")
        body = path.read_text(encoding="utf-8-sig", errors="replace")
        if "-----BEGIN " + "PRIVATE KEY-----" in body:
            errors.append(name + ": private key")
        if path.suffix == ".json":
            try:
                value = json.loads(body)
            except ValueError:
                continue
            if isinstance(value, dict) and (value.get("type") == "service_account" or "private_key" in value):
                errors.append(name + ": service-account credentials")
    if errors:
        raise SystemExit("Publication check failed:\n" + "\n".join(errors))
    print("Publication boundary checks passed. Also review staged diffs before pushing.")

if __name__ == "__main__":
    main()
