# ==============================================================================
# KỊCH BẢN KHỞI ĐỘNG & KIỂM THỬ TỰ ĐỘNG TOÀN BỘ HỆ THỐNG MYMINICLOUD (WINDOWS)
# Bao gồm: 10 bài kiểm thử Cơ bản (5.0đ) + 10 bài kiểm thử Mở rộng (5.0đ)
# ==============================================================================

$ErrorActionPreference = "Continue"
$env:PATH += ";C:\Users\Edit\AppData\Local\Programs\DockerDesktop\resources\bin"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BẮT ĐẦU KHỞI ĐỘNG VÀ KIỂM THỬ HỆ THỐNG MYMINICLOUD" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

Write-Host "`n[0] Khởi động toàn bộ cụm container bằng Docker Compose..." -ForegroundColor Yellow
docker compose up -d --build
Start-Sleep -Seconds 15
docker compose ps

Write-Host "`n[Init MinIO] Khởi tạo tự động Bucket 'demo' và 'profile-pics' trên MinIO..." -ForegroundColor Yellow
docker run --rm --network cloud-net `
  -v "${PSScriptRoot}/web-frontend-server/html:/web:ro" `
  -v "${PSScriptRoot}/object-storage-server/sample-files:/samples:ro" `
  --entrypoint /bin/sh minio/mc:latest -c "
    mc alias set myminio http://object-storage-server:9000 minioadmin minioadmin &&
    mc mb --ignore-existing myminio/demo &&
    mc mb --ignore-existing myminio/profile-pics &&
    mc anonymous set download myminio/demo &&
    mc anonymous set download myminio/profile-pics &&
    mc cp /web/index.html myminio/demo/index.html &&
    mc cp /samples/avatar.png myminio/profile-pics/avatar.png &&
    mc cp /samples/cloud_summary.pdf myminio/profile-pics/cloud_summary.pdf &&
    mc ls myminio/demo &&
    mc ls myminio/profile-pics
  "

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   PHẦN 1: KIỂM THỬ 10 YÊU CẦU CƠ BẢN (5.0 ĐIỂM)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "`n--- 1. Web Frontend Server (Nginx static site) ---" -ForegroundColor Cyan
curl.exe -I http://localhost:8080/
curl.exe -I http://localhost:8080/blog/

Write-Host "`n--- 2. Application Backend Server (Flask API /hello) ---" -ForegroundColor Cyan
curl.exe -s http://localhost:8085/hello
Write-Host ""
curl.exe -s http://localhost/api/hello
Write-Host ""

Write-Host "`n--- 3. Relational Database Server (MariaDB minicloud.notes) ---" -ForegroundColor Cyan
docker exec relational-database-server mariadb -uroot -proot -e "USE minicloud; SHOW TABLES; SELECT * FROM notes;"

Write-Host "`n--- 4. Authentication Identity Server (Keycloak HTTP Check) ---" -ForegroundColor Cyan
curl.exe -I http://localhost:8081/

Write-Host "`n--- 5. Object Storage Server (MinIO bucket 'demo') ---" -ForegroundColor Cyan
curl.exe -I http://localhost:9000/demo/index.html

Write-Host "`n--- 6. Internal DNS Server (Bind9 cloud.local) ---" -ForegroundColor Cyan
docker exec application-backend-server dig @internal-dns-server web-frontend-server.cloud.local +short

Write-Host "`n--- 7. Monitoring Prometheus + Node Exporter ---" -ForegroundColor Cyan
curl.exe -s http://localhost:9090/api/v1/targets | python -m json.tool | Select-String -Pattern "job|health|scrapeUrl"

Write-Host "`n--- 8. Monitoring Grafana Dashboard ---" -ForegroundColor Cyan
curl.exe -I http://localhost:3000/login

Write-Host "`n--- 9. API Gateway Proxy Server (Web, App, Auth qua cổng 80) ---" -ForegroundColor Cyan
curl.exe -I http://localhost/
curl.exe -s http://localhost/api/hello
Write-Host ""
curl.exe -I http://localhost/auth/

Write-Host "`n--- 10. Kiểm tra thông mạng (Ping toàn bộ 9 Server trong cloud-net) ---" -ForegroundColor Cyan
$targets = @("web", "app-server", "db", "keycloak", "minio", "prometheus", "grafana", "dns-server")
foreach ($t in $targets) {
    Write-Host "Ping $t :" -ForegroundColor Yellow
    docker exec application-backend-server ping -c 2 $t
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   PHẦN 2: KIỂM THỬ 10 YÊU CẦU MỞ RỘNG (5.0 ĐIỂM)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "`n--- Mở rộng 1: Blog cá nhân 3 bài viết (blog1, blog2, blog3) ---" -ForegroundColor Cyan
curl.exe -I http://localhost:8080/blog/blog1.html
curl.exe -I http://localhost:8080/blog/blog2.html
curl.exe -I http://localhost:8080/blog/blog3.html

Write-Host "`n--- Mở rộng 2: Backend API /student đọc file students.json ---" -ForegroundColor Cyan
curl.exe -s http://localhost/api/student
Write-Host ""

Write-Host "`n--- Mở rộng 3: Database studentdb.students & API /api/students-db ---" -ForegroundColor Cyan
docker exec relational-database-server mariadb -uroot -proot -e "USE studentdb; SELECT * FROM students;"
curl.exe -s http://localhost/api/students-db
Write-Host ""

Write-Host "`n--- Mở rộng 4: Keycloak Realm 'realm_sv001', Client 'flask-app', User 'sv01' & gọi /secure ---" -ForegroundColor Cyan
$tokenResp = curl.exe -s -X POST "http://localhost:8081/realms/realm_sv001/protocol/openid-connect/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "client_id=flask-app&username=sv01&password=123456&grant_type=password" | ConvertFrom-Json
if ($tokenResp.access_token) {
    Write-Host "Lấy Access Token thành công cho user sv01! Đang gọi /api/secure..." -ForegroundColor Green
    curl.exe -s -H "Authorization: Bearer $($tokenResp.access_token)" http://localhost/api/secure
    Write-Host ""
} else {
    Write-Host "Keycloak đang khởi động, vui lòng đợi thêm vài giây rồi thử lại." -ForegroundColor Yellow
}

Write-Host "`n--- Mở rộng 5: MinIO Bucket 'profile-pics' (avatar.png & cloud_summary.pdf) ---" -ForegroundColor Cyan
curl.exe -I http://localhost:9000/profile-pics/avatar.png
curl.exe -I http://localhost:9000/profile-pics/cloud_summary.pdf

Write-Host "`n--- Mở rộng 6: Internal DNS phân giải app-backend, minio, keycloak.cloud.local ---" -ForegroundColor Cyan
docker exec application-backend-server dig @internal-dns-server app-backend.cloud.local +short
docker exec application-backend-server dig @internal-dns-server minio.cloud.local +short
docker exec application-backend-server dig @internal-dns-server keycloak.cloud.local +short

Write-Host "`n--- Mở rộng 7: Prometheus Scrape Target 'web' (web-frontend-server:80) ---" -ForegroundColor Cyan
curl.exe -s http://localhost:8080/metrics

Write-Host "`n--- Mở rộng 8: Grafana Dashboard 'System Health of SV001' ---" -ForegroundColor Cyan
curl.exe -s -u admin:admin http://localhost:3000/api/search?query=System%20Health
Write-Host ""

Write-Host "`n--- Mở rộng 9: API Gateway Route /student/ trỏ tới Backend ---" -ForegroundColor Cyan
curl.exe -s http://localhost/student/
Write-Host ""

Write-Host "`n--- Mở rộng 10: Load Balancer Round Robin giữa web-frontend-server1 và web-frontend-server2 ---" -ForegroundColor Cyan
for ($i = 1; $i -le 4; $i++) {
    Write-Host "Request #$i qua Load Balancer (http://localhost/):" -ForegroundColor Yellow
    curl.exe -s -I http://localhost/ | Select-String -Pattern "HTTP/|X-Load-Balancer-Node"
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   HOÀN TẤT KIỂM THỬ TOÀN BỘ HỆ THỐNG MYMINICLOUD (10/10)!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

