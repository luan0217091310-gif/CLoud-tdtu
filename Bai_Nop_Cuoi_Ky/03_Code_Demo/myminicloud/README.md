# Chạy demo MyMiniCloud

## Khởi động

Dùng Docker Engine hoặc Docker Desktop ở chế độ Linux containers, Docker Compose v2.24 trở lên và Python 3.9 trở lên. Dùng Bash trên Linux, macOS hoặc WSL, hoặc PowerShell trên Windows. Mọi lệnh sau chạy tại thư mục chứa `docker-compose.yml`.

```sh
python setup_demo.py
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 220
docker compose ps
```

Để dùng MSSV của nhóm, chạy `python setup_demo.py --student-id MA_SINH_VIEN` trước khi khởi động. Khi không truyền MSSV, script dùng `DEMO0000`. Mật khẩu được tạo riêng trên máy chạy demo và được ghi vào `.env` để mở xem khi cần đăng nhập.

Nếu máy có MySQL chiếm cổng 3306, đặt cổng **máy chủ** khác trước khi chạy. Dịch vụ MariaDB và backend tiếp tục kết nối ở cổng nội bộ 3306.

```sh
export DB_HOST_PORT=13306
```

```powershell
$env:DB_HOST_PORT = "13306"
```

MinIO mặc định dùng tag công khai của Chainguard. Có thể đặt `MINIO_IMAGE` và `MINIO_CLIENT_IMAGE` thành digest đã pull; các phiên bản cụ thể của Keycloak, Prometheus, Grafana, Node Exporter và Nginx nằm trong Compose. Mạng Docker dùng `10.10.10.0/24`. Dừng bằng `docker compose down` để giữ volume. Nếu đang nâng cấp từ bản dùng đường dẫn `object-storage-server/data`, sao lưu hoặc xuất bucket trước, vì cấu hình mới dùng volume `minio-data`.

## Cổng và địa chỉ demo

| Thành phần | Địa chỉ máy chủ | Cổng container |
|---|---|---|
| Gateway | http://localhost/ | 80 |
| Web 1 và Web 2 | http://localhost:8080/ và http://localhost:8082/ | 80 |
| Flask | http://localhost:8085/hello | 8081 |
| MariaDB | 127.0.0.1:3306 | 3306 |
| Keycloak | http://localhost:8081/auth/ và http://localhost/auth/ | 8080 |
| MinIO API và Console | http://localhost:9000 và http://localhost:9001 | 9000 và 9001 |
| BIND 9 | 127.0.0.1:1053 (UDP và TCP) | 53 |
| Prometheus | http://localhost:9090/targets | 9090 |
| Node Exporter | http://localhost:9100/metrics | 9100 |
| Nginx Exporter | Qua mạng cloud-net | 9113 |
| Grafana | http://localhost:3000/ | 3000 |

Keycloak và Grafana dùng tên quản trị `admin`, MinIO dùng `minioadmin`. Xem mật khẩu tương ứng ở các biến `KC_ADMIN_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` và `MINIO_ROOT_PASSWORD` trong `.env`. Realm có hai tài khoản tổng hợp `sv01` và `sv02` với mật khẩu riêng. Giữ `.env` qua các lần chạy để thông tin đăng nhập khớp với dữ liệu trong volume.

## Kiểm thử

Chuẩn bị `object-storage-server/sample-files/avatar.jpg` và `bao-cao.pdf` theo README trong thư mục đó. Lần chạy đầy đủ tạo bucket, kiểm tra upload và dùng HEAD kiểm tra ảnh công khai. Script còn kiểm tra DNS, database, token, ba job Prometheus, hai dashboard Grafana và Round Robin. Mỗi phép thử báo PASS, FAIL hoặc SKIP. Có FAIL thì script trả mã thoát khác 0.

```bash
bash test_all.sh
```

```powershell
.\test_all.ps1
```

- Đã khởi động cụm thì thêm `--no-start`.
- Dùng `--core` để thử mã khi chưa có ảnh cá nhân. Mục E05 hiện SKIP nếu thiếu ảnh hoặc PDF.
- Tạo và cập nhật bucket riêng bằng `docker compose run --rm -T object-storage-client`.
- `docker compose logs --tail=100 <tên-service>` giúp kiểm tra lỗi khởi động.

```sh
curl http://localhost/api/student
curl http://localhost/api/students-db
curl -IL http://localhost/auth/
curl -I http://localhost:9000/profile-pics/avatar.jpg
dig @127.0.0.1 -p 1053 web-frontend-server.cloud.local +short
```

## Triển khai EC2 và Docker Hub

Dùng máy EC2 Ubuntu có public IPv4 hoặc DNS. Security Group cần SSH từ IP nhóm và HTTP 80 cho phạm vi demo. Các cổng quản trị chỉ bind loopback để có thể truy cập qua SSH tunnel. Script dùng EC2 IMDSv2 để lấy public IPv4 hoặc nhận `PUBLIC_HOST` nếu truyền vào.

```bash
bash deploy_ec2.sh
DOCKERHUB_USER="YOUR_USERNAME" bash deploy_ec2.sh --push
```

Đăng nhập Docker Hub với tài khoản có quyền push. Lệnh thứ hai đẩy `<docker-hub-user>/myminicloud-web:demo`. Có thể truyền `PUBLIC_HOST` khi cần đặt tên DNS công khai.

Ví dụ mở Grafana từ máy cá nhân qua SSH, sau đó truy cập `http://localhost:3000/`.

```bash
ssh -i <key.pem> -L 3000:127.0.0.1:3000 ubuntu@<public-host>
```
