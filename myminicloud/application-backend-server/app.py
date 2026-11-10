from flask import Flask, jsonify, request
import time, requests, os, json
from datetime import date, datetime
from jose import jwt
import pymysql

KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://authentication-identity-server:8080")
ISSUER   = os.getenv("OIDC_ISSUER",   f"{KEYCLOAK_INTERNAL_URL}/realms/master")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "myapp")

DB_HOST = os.getenv("DB_HOST", "relational-database-server")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "studentdb")

_JWKS_CACHE = {}

def get_jwks(realm="master"):
    now = time.time()
    cached = _JWKS_CACHE.get(realm)
    if not cached or now - cached["ts"] > 600:
        jwks_url = f"{KEYCLOAK_INTERNAL_URL}/realms/{realm}/protocol/openid-connect/certs"
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        _JWKS_CACHE[realm] = {"keys": resp.json(), "ts": now}
    return _JWKS_CACHE[realm]["keys"]

def get_db_connection(database=DB_NAME):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

app = Flask(__name__)

# 1. Endpoint cơ bản: /hello
@app.get("/hello")
def hello():
    return jsonify(message="Hello from App Server!")

# 2. Endpoint bảo mật OIDC (Keycloak): /secure
@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify(error="Missing Bearer token"), 401
    token = auth.split(" ", 1)[1].strip()
    try:
        unverified = jwt.get_unverified_claims(token)
        iss = unverified.get("iss", "")
        realm = iss.split("/realms/")[-1].strip("/") if "/realms/" in iss else "master"
        jwks = get_jwks(realm)
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_iss": False}
        )
        return jsonify(
            message="Secure resource OK",
            preferred_username=payload.get("preferred_username"),
            realm=realm,
            client_id=payload.get("azp", payload.get("aud"))
        )
    except Exception as e:
        return jsonify(error=str(e)), 401

# 3. Yêu cầu mở rộng 2: Endpoint đọc file tĩnh students.json (/student)
@app.get("/student")
@app.get("/student/")
def student():
    with open("students.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

# 4. Yêu cầu mở rộng 3: Endpoint CRUD kết nối MariaDB đọc/ghi/sửa/xóa bảng students trong CSDL studentdb
@app.get("/students-db")
@app.get("/api/students-db")
def get_students_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, student_id, fullname, dob, major FROM students ORDER BY id ASC")
            rows = cur.fetchall()
            for r in rows:
                if isinstance(r.get("dob"), (date, datetime)):
                    r["dob"] = r["dob"].isoformat()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/students-db")
@app.post("/api/students-db")
def add_student_db():
    body = request.get_json(force=True)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (student_id, fullname, dob, major) VALUES (%s, %s, %s, %s)",
                (body["student_id"], body["fullname"], body["dob"], body["major"])
            )
            new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify(message="Created student in MariaDB", id=new_id), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.put("/students-db/<int:student_pk>")
@app.put("/api/students-db/<int:student_pk>")
def update_student_db(student_pk):
    body = request.get_json(force=True)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE students SET fullname=%s, major=%s WHERE id=%s",
                (body["fullname"], body["major"], student_pk)
            )
        conn.commit()
        conn.close()
        return jsonify(message="Updated student in MariaDB", id=student_pk)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.delete("/students-db/<int:student_pk>")
@app.delete("/api/students-db/<int:student_pk>")
def delete_student_db(student_pk):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id=%s", (student_pk,))
        conn.commit()
        conn.close()
        return jsonify(message="Deleted student from MariaDB", id=student_pk)
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
