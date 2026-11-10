#!/usr/bin/env bash
# ==============================================================================
# KỊCH BẢN KHỞI ĐỘNG & KIỂM THỬ TỰ ĐỘNG HỆ THỐNG MYMINICLOUD (UBUNTU / AWS EC2)
# ==============================================================================
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo "   [0] KHỞI ĐỘNG TOÀN BỘ CỤM CONTAINER MYMINICLOUD"
echo "============================================================"
docker compose up -d --build
sleep 15
docker compose ps

echo ""
echo "   [Init MinIO] Tạo bucket 'demo' và 'profile-pics'..."
docker run --rm --network cloud-net \
  -v "$(pwd)/web-frontend-server/html:/web:ro" \
  -v "$(pwd)/object-storage-server/sample-files:/samples:ro" \
  --entrypoint /bin/sh minio/mc:latest -c "
    mc alias set myminio http://object-storage-server:9000 minioadmin minioadmin &&
    mc mb --ignore-existing myminio/demo &&
    mc mb --ignore-existing myminio/profile-pics &&
    mc anonymous set download myminio/demo &&
    mc anonymous set download myminio/profile-pics &&
    mc cp /web/index.html myminio/demo/index.html &&
    mc cp /samples/avatar.png myminio/profile-pics/avatar.png &&
    mc cp /samples/cloud_summary.pdf myminio/profile-pics/cloud_summary.pdf
  "

echo ""
echo "============================================================"
echo "   PHẦN 1: KIỂM THỬ 10 YÊU CẦU CƠ BẢN (5.0 ĐIỂM)"
echo "============================================================"

echo "--- 1. Web Frontend Server ---"
curl -I http://localhost:8080/
curl -I http://localhost:8080/blog/

echo "--- 2. Application Backend Server (/hello) ---"
curl -s http://localhost:8085/hello && echo ""
curl -s http://localhost/api/hello && echo ""

echo "--- 3. Relational Database Server (MariaDB minicloud.notes) ---"
docker exec relational-database-server mariadb -uroot -proot -e "USE minicloud; SHOW TABLES; SELECT * FROM notes;"

echo "--- 4. Authentication Identity Server (Keycloak) ---"
curl -I http://localhost:8081/

echo "--- 5. Object Storage Server (MinIO) ---"
curl -I http://localhost:9000/demo/index.html

echo "--- 6. Internal DNS Server (Bind9) ---"
docker exec application-backend-server dig @internal-dns-server web-frontend-server.cloud.local +short

echo "--- 7. Monitoring Prometheus + Node Exporter ---"
curl -s http://localhost:9090/api/v1/targets | grep -o '"job":"[^"]*"\|"health":"[^"]*"'

echo "--- 8. Monitoring Grafana Dashboard ---"
curl -I http://localhost:3000/login

echo "--- 9. API Gateway Proxy Server ---"
curl -I http://localhost/
curl -s http://localhost/api/hello && echo ""
curl -I http://localhost/auth/

echo "--- 10. Kiểm tra thông mạng (Ping 9 Server trong cloud-net) ---"
for host in web app-server db keycloak minio prometheus grafana dns-server; do
  docker exec application-backend-server ping -c 2 "$host"
done

echo ""
echo "============================================================"
echo "   PHẦN 2: KIỂM THỬ 10 YÊU CẦU MỞ RỘNG (5.0 ĐIỂM)"
echo "============================================================"

echo "--- Mở rộng 1: Blog cá nhân 3 bài viết ---"
curl -I http://localhost:8080/blog/blog1.html
curl -I http://localhost:8080/blog/blog2.html
curl -I http://localhost:8080/blog/blog3.html

echo "--- Mở rộng 2: API /student đọc students.json ---"
curl -s http://localhost/api/student && echo ""

echo "--- Mở rộng 3: Database studentdb.students & API /api/students-db ---"
docker exec relational-database-server mariadb -uroot -proot -e "USE studentdb; SELECT * FROM students;"
curl -s http://localhost/api/students-db && echo ""

echo "--- Mở rộng 4: Keycloak OIDC Token (realm_sv001 / flask-app / sv01) & gọi /secure ---"
TOKEN=$(curl -s -X POST "http://localhost:8081/realms/realm_sv001/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=flask-app&username=sv01&password=123456&grant_type=password" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
if [ -n "$TOKEN" ]; then
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/secure && echo ""
fi

echo "--- Mở rộng 5: MinIO Bucket profile-pics ---"
curl -I http://localhost:9000/profile-pics/avatar.png

echo "--- Mở rộng 6: Internal DNS mở rộng ---"
docker exec application-backend-server dig @internal-dns-server app-backend.cloud.local +short
docker exec application-backend-server dig @internal-dns-server minio.cloud.local +short
docker exec application-backend-server dig @internal-dns-server keycloak.cloud.local +short

echo "--- Mở rộng 7: Prometheus Scrape Target 'web' ---"
curl -s http://localhost:8080/metrics

echo "--- Mở rộng 8: Grafana Dashboard System Health of SV001 ---"
curl -s -u admin:admin "http://localhost:3000/api/search?query=System%20Health" && echo ""

echo "--- Mở rộng 9: API Gateway Route /student/ ---"
curl -s http://localhost/student/ && echo ""

echo "--- Mở rộng 10: Load Balancer Round Robin ---"
for i in 1 2 3 4; do
  echo "Request #$i:"
  curl -sI http://localhost/ | grep -E "HTTP/|X-Load-Balancer-Node"
done

echo "============================================================"
echo "   HOÀN TẤT KIỂM THỬ TOÀN BỘ HỆ THỐNG MYMINICLOUD (10/10)!"
echo "============================================================"

