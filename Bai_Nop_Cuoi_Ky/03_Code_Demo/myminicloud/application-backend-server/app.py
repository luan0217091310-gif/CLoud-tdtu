import json
import os
import time
from datetime import date, datetime
from pathlib import Path

import pymysql
import requests
from flask import Flask, jsonify, request
from jose import JWTError, jwt

KEYCLOAK_INTERNAL_URL = os.getenv(
    "KEYCLOAK_INTERNAL_URL", "http://authentication-identity-server:8080/auth"
).rstrip("/")
ALLOWED_REALMS = {
    name.strip()
    for name in os.getenv("ALLOWED_REALMS", "realm_demo0000,master").split(",")
    if name.strip()
}
LOCAL_BASES = (
    "http://localhost/auth",
    "http://localhost:8081/auth",
    "http://127.0.0.1/auth",
    "http://127.0.0.1:8081/auth",
)
PUBLIC_BASE = os.getenv("OIDC_PUBLIC_BASE_URL", "").strip().rstrip("/")
ISSUERS = {
    f"{base}/realms/{realm}": realm
    for base in (*LOCAL_BASES, PUBLIC_BASE)
    if base
    for realm in ALLOWED_REALMS
}
CLIENT_ID = "flask-app"
AUDIENCE = "flask-app"

DB_HOST = os.getenv("DB_HOST", "relational-database-server")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "studentdb")
STUDENTS_FILE = Path(__file__).with_name("students.json")
JWKS_CACHE = {}

app = Flask(__name__)
app.json.ensure_ascii = False


def get_jwks(realm):
    now = time.monotonic()
    cached = JWKS_CACHE.get(realm)
    if cached and now - cached["time"] < 300:
        return cached["jwks"]
    url = f"{KEYCLOAK_INTERNAL_URL}/realms/{realm}/protocol/openid-connect/certs"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    jwks = response.json()
    JWKS_CACHE[realm] = {"jwks": jwks, "time": now}
    return jwks


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def read_student_fields(*fields):
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Send a JSON object.")
    limits = {"student_id": 10, "fullname": 100, "major": 50, "dob": 10}
    values = []
    for field in fields:
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required.")
        value = value.strip()
        if len(value) > limits[field]:
            raise ValueError(f"{field} exceeds {limits[field]} characters.")
        if field == "dob":
            try:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() != value:
                    raise ValueError()
            except ValueError:
                raise ValueError("dob must be a valid date in YYYY-MM-DD format.") from None
        values.append(value)
    return values


@app.errorhandler(pymysql.MySQLError)
def handle_database_error(error):
    app.logger.warning("MariaDB query failed: %s", type(error).__name__)
    return jsonify(error="Database is temporarily unavailable"), 503


@app.get("/hello")
def hello():
    return jsonify(message="Hello from App Server!")


@app.get("/secure")
def secure():
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return jsonify(error="Missing Bearer token"), 401
    token = token.strip()
    try:
        issuer = jwt.get_unverified_claims(token).get("iss")
        realm = ISSUERS.get(issuer) if isinstance(issuer, str) else None
        if realm is None:
            raise JWTError("Unknown issuer")
        payload = jwt.decode(
            token,
            get_jwks(realm),
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=issuer,
            options={"require_exp": True, "require_aud": True, "require_iss": True},
        )
        if payload.get("azp") != CLIENT_ID or payload.get("typ") != "Bearer":
            raise JWTError("Unexpected client or token type")
    except (JWTError, requests.RequestException, ValueError):
        return jsonify(error="Invalid Bearer token"), 401
    return jsonify(
        message="Secure resource OK",
        preferred_username=payload.get("preferred_username"),
        realm=realm,
        client_id=CLIENT_ID,
    )


@app.get("/student")
@app.get("/student/")
def student():
    with STUDENTS_FILE.open(encoding="utf-8") as file:
        return jsonify(json.load(file))


@app.get("/students-db")
@app.get("/api/students-db")
def get_students_db():
    with get_db_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, student_id, fullname, dob, major FROM students ORDER BY id")
        rows = cursor.fetchall()
    for row in rows:
        if isinstance(row["dob"], (date, datetime)):
            row["dob"] = row["dob"].isoformat()
    return jsonify(rows)


@app.post("/students-db")
@app.post("/api/students-db")
def add_student_db():
    try:
        values = read_student_fields("student_id", "fullname", "dob", "major")
    except ValueError as error:
        return jsonify(error=str(error)), 400
    with get_db_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO students (student_id, fullname, dob, major) VALUES (%s, %s, %s, %s)",
            values,
        )
        new_id = cursor.lastrowid
        connection.commit()
    return jsonify(message="Created student in MariaDB", id=new_id), 201


@app.put("/students-db/<int:student_pk>")
@app.put("/api/students-db/<int:student_pk>")
def update_student_db(student_pk):
    try:
        values = read_student_fields("fullname", "major")
    except ValueError as error:
        return jsonify(error=str(error)), 400
    with get_db_connection() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE students SET fullname=%s, major=%s WHERE id=%s", (*values, student_pk))
        connection.commit()
    return jsonify(message="Updated student in MariaDB", id=student_pk)


@app.delete("/students-db/<int:student_pk>")
@app.delete("/api/students-db/<int:student_pk>")
def delete_student_db(student_pk):
    with get_db_connection() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM students WHERE id=%s", (student_pk,))
        connection.commit()
    return jsonify(message="Deleted student from MariaDB", id=student_pk)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
