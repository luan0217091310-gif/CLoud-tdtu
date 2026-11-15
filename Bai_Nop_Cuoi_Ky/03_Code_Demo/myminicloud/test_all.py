"""Acceptance checks for the MyMiniCloud Compose project."""

import argparse
import base64
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from setup_demo import prepare

ROOT = Path(__file__).resolve().parent
COMPOSE = ["docker", "compose"]
WEB = "http://localhost:8080"
PROXY = "http://localhost"
APP = "http://localhost:8085"
PROMETHEUS = "http://localhost:9090"
GRAFANA = "http://localhost:3000"
STORAGE = "http://localhost:9000"
AUTH = "http://localhost:8081/auth"


class CheckFailure(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def docker(*args, echo=False, timeout=45):
    result = subprocess.run(
        [*COMPOSE, *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        capture_output=not echo, timeout=timeout,
    )
    if result.returncode:
        message = result.stderr or result.stdout or ""
        raise CheckFailure(f"docker compose {args[0]} exited {result.returncode}. {message[-2000:]}")
    return (result.stdout or "").strip()


def http(url, *, method=None, data=None, headers=None, redirect=True):
    open_request = urlopen if redirect else build_opener(NoRedirect()).open
    request = Request(url, method=method, data=data, headers=headers or {})
    try:
        response = open_request(request, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def api(url, *, expected=200, method=None, body=None, headers=None):
    request_headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        request_headers["Content-Type"] = "application/json"
    status, _, content = http(url, method=method, data=data, headers=request_headers)
    require(status == expected, f"{url}: expected HTTP {expected}, received {status}.")
    return json.loads(content)


def eventually(callback, *, timeout=65):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return callback()
        except (CheckFailure, URLError, TimeoutError) as error:
            if time.monotonic() >= deadline:
                raise CheckFailure(str(error)) from error
            time.sleep(2)


def assert_page(url, title):
    status, _, body = http(url)
    require(status == 200 and title in body.decode("utf-8"), f"{url}: missing HTTP 200 or {title!r}.")
    return f"{url} → 200"


def check_frontend():
    assert_page(f"{WEB}/", "MyMiniCloud – Home")
    assert_page(f"{WEB}/blog/", "MyMiniCloud – Blog")
    _, headers, _ = http(f"{WEB}/blog", redirect=False)
    require(headers.get("Location") == "/blog/", "/blog must redirect to /blog/ on the same port.")
    return "Home and Blog return 200, /blog preserves port 8080."


def check_hello():
    expected = {"message": "Hello from App Server!"}
    require(api(f"{APP}/hello") == expected, "Direct /hello response differs.")
    require(api(f"{PROXY}/api/hello") == expected, "Proxied /api/hello response differs.")
    return expected["message"]


def check_database():
    result = docker(
        "exec", "-T", "relational-database-server", "sh", "-c",
        'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" --batch --skip-column-names '
        '-e "SELECT title FROM minicloud.notes ORDER BY id;"',
    )
    require("Hello from MariaDB!" in result.splitlines(), "Seed row missing from minicloud.notes.")
    return "minicloud.notes contains Hello from MariaDB!"


def check_auth_gateway():
    status, headers, _ = http(f"{PROXY}/auth/", redirect=False)
    require(status == 302, f"Expected /auth/ to redirect with 302, received {status}.")
    path = urlsplit(headers.get("Location", "")).path
    require(path.startswith("/auth/"), f"Redirect dropped /auth: {path!r}.")
    status, _, body = http(f"{PROXY}/auth/")
    require(status == 200 and b"keycloak" in body.lower(), "Proxied login page did not load.")
    require(http(f"{AUTH}/")[0] == 200, "Direct Keycloak admin route did not load.")
    return "302 keeps /auth, final page and direct URL return 200."


def check_storage():
    def ready():
        require(http(f"{STORAGE}/minio/health/live")[0] == 200, "MinIO is not ready yet.")

    eventually(ready)
    # mc stat verifies the upload with the authenticated S3 client.
    print("  Initializing MinIO buckets and testing stored files.", flush=True)
    docker("run", "--rm", "--no-deps", "-T", "object-storage-client", "--core",
           echo=True, timeout=180)
    return "demo, profile-pics and documents were created or already exist."


def check_dns():
    expected_records = {
        "web-frontend-server": "10.10.10.10",
        "app-backend": "10.10.10.20",
        "minio": "10.10.10.30",
        "keycloak": "10.10.10.40",
    }
    for name, expected in expected_records.items():
        result = docker("exec", "-T", "application-backend-server", "dig", "+short", "+timeout=3",
                        "+tries=1", "@internal-dns-server", f"{name}.cloud.local")
        require(result == expected, f"{name}.cloud.local: expected {expected}, got {result!r}.")
    return ", ".join(f"{key}={value}" for key, value in expected_records.items())


def prometheus_query(query):
    data = api(f"{PROMETHEUS}/api/v1/query?{urlencode({'query': query})}")
    require(data.get("status") == "success", f"Prometheus query failed: {query}.")
    return data["data"]["result"]


def check_prometheus():
    targets = api(f"{PROMETHEUS}/api/v1/targets")["data"]["activeTargets"]
    healthy = {target["labels"]["job"] for target in targets if target["health"] == "up"}
    jobs = {"node", "web", "web-nginx-exporter"}
    require(jobs <= healthy, f"Waiting for Prometheus targets: {', '.join(sorted(jobs - healthy))}.")
    require(prometheus_query("node_cpu_seconds_total"), "No CPU samples in Prometheus.")
    return "node, web and web-nginx-exporter are UP. Node CPU samples are present."


def check_dashboards(compose_env, student_id):
    credentials = base64.b64encode(
        f"{compose_env['GF_SECURITY_ADMIN_USER']}:{compose_env['GF_SECURITY_ADMIN_PASSWORD']}".encode()
    ).decode()
    dashboards = api(f"{GRAFANA}/api/search?type=dash-db", headers={"Authorization": f"Basic {credentials}"})
    titles = {item["title"] for item in dashboards}
    title = f"System Health of {student_id.upper()}"
    expected = {"Node Exporter Full", title}
    require(expected <= titles, f"Missing Grafana dashboards: {', '.join(sorted(expected - titles))}.")
    return f"Node Exporter Full + {title}"


def check_network():
    aliases = ("web", "app-server", "db", "keycloak", "minio", "prometheus", "grafana", "dns-server", "gateway")
    for alias in aliases:
        result = docker("exec", "-T", "application-backend-server", "ping", "-c", "2", "-W", "2", alias)
        require(re.search(r"\b0(?:\.0+)?% packet loss\b", result), f"{alias}: packet loss detected.")
    return f"{len(aliases)} Docker aliases answered ping without packet loss."


def check_blog():
    for page in ("blog1.html", "blog2.html", "blog3.html"):
        assert_page(f"{WEB}/blog/{page}", 'rel="stylesheet"')

    def source_tree(directory):
        result = {}
        for file in directory.rglob("*"):
            if file.is_file():
                text = file.read_text(encoding="utf-8")
                canonical = text.replace("Instance #1", "Instance").replace("Instance #2", "Instance")
                result[file.relative_to(directory)] = canonical
        return result

    first, second = (ROOT / f"{node}/html" for node in ("web-frontend-server", "web-frontend-server2"))
    require(source_tree(first) == source_tree(second), "Web replicas differ outside their instance label.")
    return "Three articles load. Web copies match except the node label."


def student_list(path):
    rows = api(f"{PROXY}/{path}")
    fields = {"id", "name", "major", "gpa"}
    require(isinstance(rows, list) and len(rows) == 5 and all(fields <= row.keys() for row in rows),
            f"/{path} must return five records with id, name, major and gpa.")
    return rows


def check_students_db():
    url = f"{PROXY}/api/students-db"
    rows = api(url)
    require(isinstance(rows, list) and len(rows) >= 3, "studentdb.students has fewer than 3 rows.")
    api(url, expected=400, method="POST", body={})
    api(f"{url}/1", expected=400, method="PUT", body={"fullname": "Missing major"})
    value = {"student_id": "SMOKETEST", "fullname": "Synthetic test record", "dob": "2000-01-01", "major": "Cloud"}
    created = api(url, expected=201, method="POST", body=value)
    record_url = f"{url}/{created['id']}"
    try:
        api(record_url, method="PUT", body={"fullname": value["fullname"], "major": "Testing"})
        updated = next((row for row in api(url) if row["id"] == created["id"]), None)
        require(updated and updated["major"] == "Testing", "PUT did not persist the change.")
    finally:
        api(record_url, method="DELETE")
    require(all(row["id"] != created["id"] for row in api(url)), "DELETE did not remove the test row.")
    return "SQL seed, CRUD and 400 validation checked."


def check_token(auth_env):
    realm = f"realm_{auth_env['DEMO_STUDENT_ID']}"
    body = urlencode({"client_id": "flask-app", "grant_type": "password", "username": "sv01",
                      "password": auth_env["DEMO_SV01_PASSWORD"]}).encode()
    for base in (AUTH, f"{PROXY}/auth"):
        url = f"{base}/realms/{realm}/protocol/openid-connect/token"
        status, _, reply = http(url, method="POST", data=body,
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
        require(status == 200, f"Token endpoint at {base} returned {status}.")
        token = json.loads(reply)["access_token"]
        flags = {"Authorization": f"Bearer {token}"}
        decoded = api(f"{PROXY}/api/secure", headers=flags)
        require(decoded.get("preferred_username") == "sv01" and decoded.get("message") == "Secure resource OK",
                f"/api/secure did not accept the test user's access token from {base}.")
    api(f"{PROXY}/api/secure", expected=401, headers={"Authorization": "Bearer invalid-token"})
    api(f"{PROXY}/api/secure", expected=401)
    return "Direct and proxied issuers accepted, missing and invalid tokens return 401."


def check_avatar():
    samples = ROOT / "object-storage-server/sample-files"
    require((samples / "bao-cao.pdf").is_file(), "Export the Word report as sample-files/bao-cao.pdf.")
    require((samples / "avatar.jpg").is_file(), "Copy a real JPEG to sample-files/avatar.jpg.")
    status, headers, _ = http(f"{STORAGE}/profile-pics/avatar.jpg", method="HEAD")
    require(status == 200 and headers.get_content_type() == "image/jpeg",
            "Expected public JPEG at /profile-pics/avatar.jpg. Supply a real avatar and run the storage initializer.")
    return f"{STORAGE}/profile-pics/avatar.jpg → 200"


def check_web_metrics():
    _, _, body = http(f"{WEB}/metrics")
    require(b"nginx_up 1" in body and b"nginx_http_requests_total" not in body,
            "The direct web target must serve the health gauge only.")
    expression = 'nginx_http_requests_total{job="web-nginx-exporter"}'
    require(prometheus_query(expression), "Prometheus has not yet collected Nginx request counts.")
    return "Health probe plus real Nginx request counter scraped."


def check_balancer():
    expected = {"web-frontend-server1", "web-frontend-server2"}
    nodes = []
    for _ in range(4):
        status, headers, body = http(f"{PROXY}/")
        node = headers.get("X-Load-Balancer-Node")
        require(status == 200 and node in expected, "Round Robin response did not identify its frontend.")
        require(f"Instance #{node[-1]}".encode() in body, "Node response header and page disagree.")
        nodes.append(node)
    require(set(nodes) == expected and all(a != b for a, b in zip(nodes, nodes[1:])),
            f"Expected alternation, got {', '.join(nodes)}.")
    return " → ".join(f"Instance #{node[-1]}" for node in nodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", action="store_true", help="Run without personal evidence files.")
    parser.add_argument("--no-start", action="store_true", help="Test a Compose stack already running.")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if not args.no_start:
            prepare()
        config = json.loads(docker("config", "--format", "json"))
        if not args.no_start:
            docker("up", "-d", "--build", "--wait", "--wait-timeout", "220", echo=True, timeout=480)
        eventually(lambda: assert_page(f"{PROXY}/", "MyMiniCloud – Home"))
    except (CheckFailure, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"FAIL [startup] {error}", file=sys.stderr)
        return 1

    grafana_env = config["services"]["monitoring-grafana-dashboard-server"]["environment"]
    auth_env = config["services"]["authentication-identity-server"]["environment"]
    checks = [
        ("B01", "Frontend", check_frontend),
        ("B02", "Flask /hello", check_hello),
        ("B03", "MariaDB / notes", check_database),
        ("B04/B09", "Keycloak and gateway", check_auth_gateway),
        ("B05", "MinIO buckets and object uploads", check_storage),
        ("B06/E06", "BIND zone", check_dns),
        ("B07/E07", "Prometheus targets and Nginx metrics",
         lambda: eventually(lambda: (check_prometheus(), check_web_metrics()))[-1]),
        ("B08/E08", "Grafana dashboards", lambda: eventually(lambda: check_dashboards(grafana_env, auth_env["DEMO_STUDENT_ID"]))),
        ("B10", "Docker network", check_network),
        ("E01", "Blog and replica parity", check_blog),
        ("E02/E09", "JSON student API and gateway routes",
         lambda: require(student_list("api/student") == student_list("student/"), "Student routes disagree.")),
        ("E03", "MariaDB student CRUD", check_students_db),
        ("E04", "Keycloak access token", lambda: check_token(auth_env)),
        ("E05", "Public avatar", check_avatar),
        ("E10", "Round Robin", check_balancer),
    ]
    passed = failed = skipped = 0
    for code, name, callback in checks:
        samples = ROOT / "object-storage-server/sample-files"
        if code == "E05" and args.core and not all((samples / name).is_file() for name in ("avatar.jpg", "bao-cao.pdf")):
            print(f"SKIP [{code}] {name} | supply avatar.jpg and bao-cao.pdf for the full check.", flush=True)
            skipped += 1
            continue
        try:
            detail = callback()
        except (CheckFailure, URLError, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
            print(f"FAIL [{code}] {name} | {error}", flush=True)
            failed += 1
        else:
            print(f"PASS [{code}] {name}" + (f" | {detail}" if detail else ""), flush=True)
            passed += 1
    print(f"Summary: {passed} PASS, {failed} FAIL, {skipped} SKIP")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
