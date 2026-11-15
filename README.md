# ☁️ MYMINICLOUD - MÔ PHỎNG HỆ THỐNG ĐIỆN TOÁN ĐÁM MÂY

> **ĐỒ ÁN CUỐI KỲ HỌC PHẦN ĐIỆN TOÁN ĐÁM MÂY (504087)**  
> **TRƯỜNG ĐẠI HỌC TÔN ĐỨC THẮNG (TDTU) - KHOA CÔNG NGHỆ THÔNG TIN**  
> **Giảng viên hướng dẫn:** TS. Bùi Quý Anh  
>
> 🎥 **Video Demo Nghiệm Thu (Google Drive):** [Thư mục Video Demo (Public)](https://drive.google.com/drive/folders/1YqE38wqXnMCx1MyFPCY58pH5lnIvunB8?usp=sharing)  
> 🌐 **AWS EC2 Public Gateway (Live):** [http://47.129.198.197/](http://47.129.198.197/) (`ec2-47-129-198-197.ap-southeast-1.compute.amazonaws.com`)  
> 📄 **Báo Cáo Cuối Kỳ (Word .docx):** [MyMiniCloud_Final_Report.docx](Bai_Nop_Cuoi_Ky/01_Bao_Cao/MyMiniCloud_Final_Report.docx)  
> 📊 **Slide Thuyết Trình (PowerPoint .pptx):** [MyMiniCloud_Presentation.pptx](Bai_Nop_Cuoi_Ky/02_Slide/MyMiniCloud_Presentation.pptx)  
> 💻 **Mã Nguồn & Kịch Bản Kiểm Thử:** [Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud](Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud/)

Hệ thống **MyMiniCloud** được thiết kế và xây dựng nhằm mô phỏng một nền tảng Cloud Platform thu nhỏ hoàn chỉnh (tương đương AWS, GCP, Azure) gồm **9 loại máy chủ cốt lõi** và **10 tính năng mở rộng thực tế**, vận hành trong các Docker container độc lập, kết nối qua mạng nội bộ `cloud-net` (Subnet: `10.10.10.0/24`) và được triển khai, kiểm thử tự động (**15/15 PASS**) trên cả **máy Local** lẫn **AWS EC2 (Ubuntu LTS)**.

---

## 👥 THÔNG TIN SINH VIÊN THỰC HIỆN

| STT | Họ và Tên | Mã số sinh viên (MSSV) | Vai trò & Phụ trách kỹ thuật |
| :---: | :--- | :---: | :--- |
| **1** | **Phùng Hữu Luân** | **524H0167** | **Nhóm trưởng — Kiến trúc Hạ tầng, API Gateway, Xác thực & Triển khai AWS EC2:**<br>- Thiết kế mạng nội bộ `cloud-net` (`10.10.10.0/24`) & điều phối `docker-compose.yml`<br>- Nginx API Gateway & Cân bằng tải Round Robin (`web-frontend-server` & `web-frontend-server2`)<br>- Keycloak OIDC Identity Provider (`realm_524h0167`, client `flask-app`, users `sv01`/`sv02`)<br>- Triển khai thực tế trên AWS EC2 (`47.129.198.197`), cấu hình Swap RAM 4GB & Phát hành Docker Hub (`bekanesiucapcute`) |
| **2** | **Ngô Bình Minh** | **524H0169** | **Phụ trách Web Frontend, Application Backend & Cơ sở dữ liệu:**<br>- Xây dựng 2 node Web Frontend tĩnh & Blog kỹ thuật 3 bài viết có minh họa SVG (`blog1.html`, `blog2.html`, `blog3.html`)<br>- Phát triển Flask REST API Server (`/hello`, `/student`, `/students-db`, `/secure` xác thực RS256 JWKS)<br>- Khởi tạo CSDL MariaDB (`minicloud.notes` & `studentdb.students`) và kiểm thử CRUD / HTTP 400 validation |
| **3** | **Ngô Đặng Trọng Hiếu** | **524H0050** | **Phụ trách Lưu trữ Object Storage, DNS nội bộ & Giám sát Observability:**<br>- Cấu hình MinIO Object Storage & container khởi tạo tự động 3 buckets (`demo`, `profile-pics/avatar.jpg` public, `documents/bao-cao.pdf`)<br>- Cấu hình BIND 9 Internal DNS Server (`cloud.local` zone cho `web-frontend-server`, `app-backend`, `minio`, `keycloak`)<br>- Thiết lập Prometheus + Node Exporter + Nginx Exporter & Grafana Dashboard (`System Health of 524H0167` và `Node Exporter Full`) |

---

## 🗺️ BẢN ĐỒ MẠNG & PHÂN ĐỊNH DỊCH VỤ (`cloud-net: 10.10.10.0/24`)

| STT | Tên Service | Container Name | IP Nội Bộ | Cổng Host Exposed | Chức Năng & Vai Trò |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | `api-gateway-proxy-server` | `api-gateway-proxy-server` | `10.10.10.80` | `80:80` | Reverse Proxy gom cổng (`/`, `/api/`, `/student/`, `/auth/`) & Round Robin Load Balancer |
| **2** | `web-frontend-server` | `web-frontend-server` | `10.10.10.10` | `8080:80` | Web Frontend Node 1 (`Instance #1` — Trang chủ & Blog 3 bài viết) |
| **3** | `web-frontend-server2` | `web-frontend-server2` | `10.10.10.11` | `8082:80` | Web Frontend Node 2 (`Instance #2` — Đối tác cân bằng tải Round Robin) |
| **4** | `application-backend-server` | `application-backend-server` | `10.10.10.20` | `8085:8081` | Flask REST API Server (`/hello`, `/student`, `/students-db`, `/secure`) |
| **5** | `object-storage-server` | `object-storage-server` | `10.10.10.30` | `9000:9000`<br>`9001:9001` | MinIO Object Storage tương thích S3 (`demo`, `profile-pics`, `documents`) |
| **6** | `authentication-identity-server` | `authentication-identity-server` | `10.10.10.40` | `8081:8080` | Keycloak Identity Provider OIDC/JWT (`realm_524h0167`) |
| **7** | `relational-database-server` | `relational-database-server` | `10.10.10.50` | `3306:3306` | MariaDB RDS (`minicloud` bảng `notes` & `studentdb` bảng `students`) |
| **8** | `internal-dns-server` | `internal-dns-server` | `10.10.10.53` | `1053:53/udp,tcp` | BIND 9 DNS phân giải tên miền nội bộ `*.cloud.local` |
| **9** | `monitoring-prometheus-server` | `monitoring-prometheus-server` | `10.10.10.60` | `9090:9090` | Thu thập metrics từ `node`, `web` và `web-nginx-exporter` |
| **10** | `monitoring-grafana-dashboard-server` | `monitoring-grafana-dashboard-server` | `10.10.10.70` | `3000:3000` | Trực quan hóa dữ liệu với Dashboard `System Health of 524H0167` & `Node Exporter Full` |
| **11** | `monitoring-node-exporter-server` & `monitoring-nginx-exporter-server` | `monitoring-node-exporter-server`<br>`monitoring-nginx-exporter-server` | `cloud-net` | `9100:9100`<br>`9113` (nội bộ) | Xuất thông số phần cứng Linux (CPU/RAM/Network) và bộ đếm request Nginx |

---

## 📦 DOCKER HUB REGISTRY

Ba Docker Images tùy chỉnh của nhóm đã được đóng gói và phát hành công khai (Public) trên Docker Hub dưới tài khoản **`bekanesiucapcute`**:

- 🌐 **Web Frontend Node 1:** [`bekanesiucapcute/myminicloud-web:demo`](https://hub.docker.com/r/bekanesiucapcute/myminicloud-web) (`sha256:13f02d61464b2f410aab358fad486a44b5399eeee823d93e1958b6273c8b84ac`)
- 🌐 **Web Frontend Node 2:** [`bekanesiucapcute/myminicloud-web2:demo`](https://hub.docker.com/r/bekanesiucapcute/myminicloud-web2) (`sha256:e8809c1369c2a0cf75a2fe3613301bdd5259a95d6bcf9976b2473e2da3166df8`)
- ⚙️ **Application Backend API:** [`bekanesiucapcute/myminicloud-app:demo`](https://hub.docker.com/r/bekanesiucapcute/myminicloud-app) (`sha256:87f5a173c4c063a6a0c0de4b95ae7823567266696fe6338a219c15ba07dfb7b3`)

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY & KIỂM THỬ TỰ ĐỘNG (15/15 PASS)

### 1. Khởi chạy toàn bộ cụm dịch vụ tại máy Local
Di chuyển vào thư mục mã nguồn `Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud`:

```powershell
cd Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud

# 1. Sinh thông tin xác thực .env, Keycloak realm_524h0167 và Grafana Dashboard System Health of 524H0167
python setup_demo.py --student-id 524H0167

# 2. Khởi chạy toàn bộ cụm container và chờ trạng thái Healthy
docker compose up -d --build --wait --wait-timeout 220

# 3. Khởi tạo 3 buckets MinIO (demo, profile-pics, documents) và upload avatar.jpg + bao-cao.pdf
docker compose run --rm --no-deps -T object-storage-client
```

### 2. Chạy kịch bản kiểm thử nghiệm thu tự động (15 bài kiểm tra)
```powershell
# Trên Windows PowerShell:
.\test_all.ps1 --no-start

# Trên Linux / WSL / macOS:
bash test_all.sh --no-start
```

**Kết quả thực chạy (`test-results.txt`):**
```text
PASS [B01] Frontend | Home and Blog return 200, /blog preserves port 8080.
PASS [B02] Flask /hello | Hello from App Server!
PASS [B03] MariaDB / notes | minicloud.notes contains Hello from MariaDB!
PASS [B04/B09] Keycloak and gateway | 302 keeps /auth, final page and direct URL return 200.
PASS [B05] MinIO buckets and object uploads | demo, profile-pics and documents were created or already exist.
PASS [B06/E06] BIND zone | web-frontend-server=10.10.10.10, app-backend=10.10.10.20, minio=10.10.10.30, keycloak=10.10.10.40
PASS [B07/E07] Prometheus targets and Nginx metrics | Health probe plus real Nginx request counter scraped.
PASS [B08/E08] Grafana dashboards | Node Exporter Full + System Health of 524H0167
PASS [B10] Docker network | 9 Docker aliases answered ping without packet loss.
PASS [E01] Blog and replica parity | Three articles load. Web copies match except the node label.
PASS [E02/E09] JSON student API and gateway routes
PASS [E03] MariaDB student CRUD | SQL seed, CRUD and 400 validation checked.
PASS [E04] Keycloak access token | Direct and proxied issuers accepted, missing and invalid tokens return 401.
PASS [E05] Public avatar | http://localhost:9000/profile-pics/avatar.jpg → 200
PASS [E10] Round Robin | Instance #1 → Instance #2 → Instance #1 → Instance #2
Summary: 15 PASS, 0 FAIL, 0 SKIP
```

---

## 🔍 KỊCH BẢN KIỂM THỬ CHI TIẾT TỪNG DỊCH VỤ

1. **Web Frontend & Blog 3 bài viết (Cơ bản 1 & Mở rộng 1):**
   - Node 1: `http://localhost:8080/` và `http://localhost:8080/blog/` (`blog1.html`, `blog2.html`, `blog3.html`)
   - Node 2: `http://localhost:8082/`
2. **Application Backend API (Cơ bản 2 & Mở rộng 2):**
   - Trực tiếp: `curl http://localhost:8085/hello` → `{"message":"Hello from App Server!"}`
   - Qua Gateway: `curl http://localhost/api/hello`
   - Danh sách 5 sinh viên JSON: `curl http://localhost/api/student` (gồm Phùng Hữu Luân `524H0167`, Ngô Bình Minh `524H0169`, Ngô Đặng Trọng Hiếu `524H0050`).
3. **Relational Database MariaDB (Cơ bản 3 & Mở rộng 3):**
   - API kết nối trực tiếp MariaDB (`studentdb.students`): `curl http://localhost/api/students-db`
   - Truy vấn CLI: `docker compose exec relational-database-server mariadb -uroot -p -e "SELECT * FROM minicloud.notes; SELECT * FROM studentdb.students;"`
4. **Authentication & Identity Keycloak (Cơ bản 4 & Mở rộng 4):**
   - Giao diện quản trị: `http://localhost:8081/auth/` hoặc `http://localhost/auth/`
   - Realm `realm_524h0167`, Client `flask-app` (public), Users `sv01` và `sv02` bảo vệ endpoint `/api/secure`.
5. **Object Storage MinIO (Cơ bản 5 & Mở rộng 5):**
   - MinIO Console: `http://localhost:9001` (Buckets: `demo`, `profile-pics`, `documents`)
   - Ảnh đại diện công khai: `curl -I http://localhost:9000/profile-pics/avatar.jpg` (`HTTP/1.1 200 OK`, `image/jpeg`)
6. **Internal DNS BIND 9 (Cơ bản 6 & Mở rộng 6):**
   - Phân giải 4 bản ghi nội bộ (`web-frontend-server`, `app-backend`, `minio`, `keycloak`):
     `dig @127.0.0.1 -p 1053 web-frontend-server.cloud.local +short` → `10.10.10.10`
7. **Monitoring Prometheus & Exporters (Cơ bản 7 & Mở rộng 7):**
   - Kiểm tra 3 targets (`node`, `web`, `web-nginx-exporter`) ở trạng thái **UP**: `http://localhost:9090/targets`
8. **Grafana Dashboard (Cơ bản 8 & Mở rộng 8):**
   - Xem trực tiếp Dashboard **`System Health of 524H0167`** (3 biểu đồ CPU Usage, Memory Used, Network Traffic): `http://localhost:3000/d/system-health-524h0167/system-health-of-524h0167`
9. **API Gateway Route `/student/` & Round Robin Load Balancer (Cơ bản 9, Mở rộng 9 & 10):**
   - Route `/student/`: `curl http://localhost/student/`
   - Kiểm tra cân bằng tải luân phiên: `curl -I http://localhost/` (Header `X-Load-Balancer-Node` đổi luân phiên `web-frontend-server1` và `web-frontend-server2`).

---

## ☁️ TRIỂN KHAI TRÊN AWS EC2 (`47.129.198.197`)

Hệ thống đã được triển khai thực tế trên máy ảo **AWS EC2 Ubuntu 26.04 LTS** (`Instance ID: i-02017cafcd74a7368`, Region `ap-southeast-1c`) thông qua script tự động `deploy_ec2.sh` (tự động cài đặt Docker, tạo 4GB Swap RAM chống tràn bộ nhớ, cấu hình realm `524h0167` và khởi chạy toàn bộ cụm container):

```bash
git clone https://github.com/luan0217091310-gif/CLoud-tdtu.git
cd CLoud-tdtu/Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud
PUBLIC_HOST=47.129.198.197 bash deploy_ec2.sh
sudo docker compose run --rm --no-deps -T object-storage-client
```

**Các liên kết kiểm tra trực tiếp trên AWS EC2:**
- Trang chủ & Load Balancer: [http://47.129.198.197/](http://47.129.198.197/)
- Trang Blog: [http://47.129.198.197/blog/](http://47.129.198.197/blog/)
- API `/api/hello`: [http://47.129.198.197/api/hello](http://47.129.198.197/api/hello)
- API `/api/student` (JSON): [http://47.129.198.197/api/student](http://47.129.198.197/api/student)
- API `/student/` (Gateway Route): [http://47.129.198.197/student/](http://47.129.198.197/student/)
- API `/api/students-db` (MariaDB): [http://47.129.198.197/api/students-db](http://47.129.198.197/api/students-db)
- Keycloak OIDC: [http://47.129.198.197/auth/](http://47.129.198.197/auth/)

---

## 🏆 TỔNG KẾT MỨC ĐỘ HOÀN THÀNH

- [x] **9/9 Máy chủ cơ bản trên mạng `cloud-net` (5.0 / 5.0 Điểm)**
- [x] **10/10 Yêu cầu mở rộng ứng dụng thực tế — `15 PASS, 0 FAIL, 0 SKIP` (5.0 / 5.0 Điểm)**
- [x] **Đóng gói và phát hành 3 Custom Images lên Docker Hub (`bekanesiucapcute`)**
- [x] **Triển khai và nghiệm thu thực tế trên AWS EC2 (`http://47.129.198.197/`)**
- [x] **Báo cáo Word (đầy đủ 11 hình minh chứng thực tế) & Slide thuyết trình hoàn chỉnh**
