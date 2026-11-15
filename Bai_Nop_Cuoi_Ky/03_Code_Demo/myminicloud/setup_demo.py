"""Create local credentials and materialize the Keycloak and Grafana templates."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
RUNTIME = ROOT / ".demo"
PASSWORD_KEYS = (
    "MARIADB_ROOT_PASSWORD",
    "KC_ADMIN_PASSWORD",
    "MINIO_ROOT_PASSWORD",
    "GRAFANA_ADMIN_PASSWORD",
    "DEMO_SV01_PASSWORD",
    "DEMO_SV02_PASSWORD",
)


def read_env():
    if not ENV_FILE.exists():
        return {}
    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def write_env(values):
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=ROOT, prefix=".env.", delete=False,
    ) as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")
        temporary = Path(handle.name)
    try:
        temporary.chmod(0o600)
        temporary.replace(ENV_FILE)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare(student_id=None):
    existing = read_env()
    values = existing.copy()
    if student_id is None:
        student_id = os.getenv("DEMO_STUDENT_ID") or values.get("DEMO_STUDENT_ID") or "demo0000"
    if not re.fullmatch("[A-Za-z0-9]{1,16}", student_id):
        raise ValueError("The student ID must contain 1 to 16 letters or numbers.")
    suffix = student_id.lower()
    values["DEMO_STUDENT_ID"] = suffix
    for key in PASSWORD_KEYS:
        if not values.get(key):
            values[key] = secrets.token_hex(18)
    if values != existing:
        write_env(values)

    realm_name = f"realm_{suffix}"
    realm_src = ROOT / "authentication-identity-server/realm-template.json"
    realm = json.loads(realm_src.read_text(encoding="utf-8"))
    realm["realm"] = realm_name
    realm["displayName"] = f"MyMiniCloud OIDC ({suffix.upper()})"
    imports = RUNTIME / "realms"
    write_json(imports / f"{realm_name}-realm.json", realm)
    for old in imports.glob("realm_*-realm.json"):
        if old.name != f"{realm_name}-realm.json":
            old.unlink()

    templates = ROOT / "monitoring-grafana-dashboard-server/dashboard-templates"
    dashboards = RUNTIME / "dashboards"
    health = json.loads((templates / "system-health.json").read_text(encoding="utf-8"))
    health.update(uid=f"system-health-{suffix}", title=f"System Health of {suffix.upper()}")
    write_json(dashboards / "system-health.json", health)
    shutil.copyfile(templates / "node-exporter-full.json", dashboards / "node-exporter-full.json")
    return suffix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-id", help="Student ID for the realm and the custom Grafana dashboard.")
    args = parser.parse_args()
    try:
        suffix = prepare(args.student_id)
    except ValueError as error:
        parser.error(str(error))
    print(f"Configured realm_{suffix} and System Health of {suffix.upper()}.")
    print("Open the local .env file to read the generated demo credentials.")


if __name__ == "__main__":
    main()
