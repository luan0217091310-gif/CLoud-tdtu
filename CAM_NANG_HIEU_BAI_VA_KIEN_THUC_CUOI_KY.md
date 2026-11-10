# 🎓 CẨM NANG HIỂU BẢN CHẤT ĐỒ ÁN CUỐI KỲ, TỔNG HỢP KIẾN THỨC & VIỆC CẦN LÀM

File này được biên soạn riêng để giúp bạn **hiểu nhanh, hiểu sâu bản chất** đồ án cuối kỳ môn **Điện toán đám mây (Course ID: 504087)** chỉ trong 10–15 phút đọc, nắm vững kiến thức để tự tin chỉnh sửa báo cáo hoặc trả lời vấn đáp với giảng viên.

---

## PHẦN 1: BÀI TẬP CUỐI KỲ NÀY THỰC CHẤT LÀ LÀM CÁI GÌ? (Hiểu trong 2 phút)

### 1. Ý tưởng cốt lõi
Trong suốt môn học, bạn đã học lý thuyết (9 Chương) và thực hành trên đám mây thật của **Amazon Web Services - AWS** (như tạo máy ảo **EC2**, lưu file **S3**, chạy web **Elastic Beanstalk**, tạo **Blog WordPress**...).

Ở bài cuối kỳ này, thay vì thuê rời rạc từng dịch vụ trên mạng, đề bài yêu cầu bạn **tự tay xây dựng một "Đám mây thu nhỏ" của riêng mình (gọi là `MyMiniCloud`)** ngay bên trong máy tính (hoặc trên 1 máy chủ AWS EC2) bằng công nghệ **Docker Container**.

### 2. Tại sao lại có 9 loại Server?
Một nền tảng đám mây thực tế (như AWS, Azure, Google Cloud) luôn phải có đủ các mảnh ghép: chỗ chứa web, chỗ chạy code xử lý, chỗ lưu dữ liệu bảng, chỗ lưu file/ảnh, chỗ quản lý đăng nhập, chỗ phân giải tên miền, chỗ theo dõi sức khỏe máy chủ và một "cổng bảo vệ" điều phối bên ngoài.

Do đó, `MyMiniCloud` mô phỏng lại đúng **9 mảnh ghép (9 máy chủ chạy trong 9 container riêng biệt)** kết nối chung vào 1 mạng dây nội bộ ảo tên là **`cloud-net`**:

| STT | Tên Server trong bài | Đóng vai trò gì? (Giải thích bình dân) | Tương ứng dịch vụ nào trên AWS / Thực tế? |
| :-: | :--- | :--- | :--- |
| **1** | **`web-frontend-server`** *(Nginx)* | **Máy chủ giao diện Web tĩnh:** Chứa các trang HTML, CSS, hình ảnh và trang Blog cá nhân (`/blog/`) để người dùng đọc. | AWS S3 Static Web Hosting / WordPress (Lab 2) |
| **2** | **`application-backend-server`** *(Flask Python)* | **Máy chủ xử lý logic (API):** Chạy code Python trả về dữ liệu JSON (`/hello`, `/student`), kiểm tra thẻ đăng nhập (`/secure`) và lấy dữ liệu từ Database (`/students-db`). | AWS Elastic Beanstalk (Lab 7, 8) / AWS Lambda |
| **3** | **`relational-database-server`** *(MariaDB)* | **Máy chủ Cơ sở dữ liệu dạng bảng (SQL):** Lưu trữ dữ liệu có cấu trúc dạng hàng-cột (bảng `notes`, bảng sinh viên `students`). | Amazon RDS (MySQL / MariaDB) |
| **4** | **`authentication-identity-server`** *(Keycloak)* | **Máy chủ Đăng nhập & Cấp thẻ (SSO/OIDC):** Quản lý tài khoản người dùng (`sv01`, `sv02`). Khi đăng nhập đúng, nó cấp 1 "thẻ thông hành điện tử" (**JWT Access Token**) để mang đi gọi API bảo mật. | AWS Cognito / Google Sign-In (Chương 6 - IDaaS) |
| **5** | **`object-storage-server`** *(MinIO)* | **Máy chủ Lưu trữ File & Ảnh (Object Storage):** Không lưu dạng bảng SQL mà lưu từng cục file (ảnh đại diện `avatar.png`, file `.pdf`, `.html`) vào các "xô chứa" gọi là **Bucket** (`demo`, `profile-pics`). | Amazon S3 (Lab 5) / Dropbox (Lab 1) |
| **6** | **`internal-dns-server`** *(Bind9)* | **Máy chủ Danh bạ Tên miền nội bộ (DNS):** Giúp dịch tên miền nội bộ (như `web-frontend-server.cloud.local`, `app-backend.cloud.local`) ra địa chỉ IP (`10.10.10.10`, `10.10.10.20`). | Amazon Route 53 (Private Hosted Zone) |
| **7** | **`monitoring-prometheus-server`** *(+ Node Exporter)* | **Máy chủ Thu thập chỉ số sức khỏe:** `Node Exporter` đo thông số CPU, RAM, Mạng của máy chủ; cứ mỗi 15 giây `Prometheus` sẽ tự động đi "hỏi thăm" (scrape) và lưu lại lịch sử các con số này. | Amazon CloudWatch Metrics |
| **8** | **`monitoring-grafana-dashboard-server`** *(Grafana)* | **Máy chủ Vẽ biểu đồ giám sát:** Lấy các con số khô khan từ Prometheus để vẽ thành biểu đồ đường/cột trực quan đẹp mắt (Dashboard *System Health*). | Amazon Managed Grafana / CloudWatch Dashboard |
| **9** | **`api-gateway-proxy-server`** *(Nginx Proxy)* | **Cổng điều phối duy nhất (Lễ tân & Cân bằng tải):** Đứng ở cổng `80`. Khách bên ngoài chỉ cần gọi vào cổng 80 này, nó sẽ tự động dẫn đường: hỏi web thì đưa vào Server 1, hỏi `/api/` thì đưa vào Server 2, hỏi `/auth/` thì đưa vào Server 4. | Amazon API Gateway + Elastic Load Balancer (ALB) |

---

## PHẦN 2: KHÁI QUÁT CÁC KIẾN THỨC CỐT LÕI TRONG BÀI (Để hiểu bản chất & trả lời thầy cô)

### 1. Ba mô hình dịch vụ đám mây: IaaS – PaaS – SaaS (và IDaaS)
- **IaaS (Infrastructure as a Service – Hạ tầng hướng dịch vụ):** Thuê phần cứng ảo hóa (máy ảo, ổ cứng, mạng, DNS). Bạn phải tự cài hệ điều hành và phần mềm.
  - *Trong bài:* Máy ảo **AWS EC2**, mạng `cloud-net`, lưu trữ **MinIO S3**, DNS **Bind9**.
- **PaaS (Platform as a Service – Nền tảng hướng dịch vụ):** Môi trường đã dựng sẵn runtime (Python, Database) để lập trình viên chỉ việc đưa code lên chạy.
  - *Trong bài:* **Flask Backend API** (`application-backend-server`) và **MariaDB** (`relational-database-server`), tương tự **AWS Elastic Beanstalk** ở Lab 7–8.
- **SaaS (Software as a Service – Phần mềm hướng dịch vụ):** Phần mềm hoàn chỉnh mở trình duyệt là dùng ngay, không cần biết code bên dưới.
  - *Trong bài:* Giao diện **Blog cá nhân**, giao diện **Grafana Dashboard**, **MinIO Console** (tương tự Dropbox ở Lab 1, WordPress ở Lab 2, CRM ở Lab 3).
- **IDaaS (Identity as a Service – Định danh hướng dịch vụ):** Dịch vụ chuyên trách việc đăng nhập và phân quyền tập trung.
  - *Trong bài:* **Keycloak** (`authentication-identity-server`).

### 2. Ảo hóa (Virtualization) vs Container hóa (Docker & Docker Compose)
- **Máy ảo truyền thống (VM - như EC2/VirtualBox):** Mỗi máy ảo phải cài nguyên một Hệ điều hành riêng (Guest OS nặng hàng GB), khởi động mất vài phút.
- **Container (Docker):** Dùng chung nhân hệ điều hành (Linux Kernel) của máy gốc, chỉ đóng gói đúng ứng dụng và thư viện cần thiết (nhẹ vài chục MB, bật lên trong 1–2 giây).
- **Docker Compose (`docker-compose.yml`):** Thay vì phải gõ 10 lệnh `docker run` dài dòng để bật 10 máy chủ, ta viết toàn bộ cấu hình vào 1 file `docker-compose.yml` và chỉ cần gõ `docker compose up -d` là cả "đám mây" 9 server tự động bật lên và nối mạng với nhau.

### 3. Cơ chế Reverse Proxy, API Gateway & Cân bằng tải (Load Balancing)
- **Reverse Proxy / API Gateway (Server 9):** Giấu toàn bộ các máy chủ bên trong để bảo mật. Người dùng chỉ giao tiếp với cổng `80`:
  - Gọi `http://localhost/` $\rightarrow$ Chuyển vào `web-frontend-server:80`
  - Gọi `http://localhost/api/hello` $\rightarrow$ Cắt bỏ chữ `/api/` và chuyển vào `application-backend-server:8081/hello`
  - Gọi `http://localhost/student/` $\rightarrow$ Chuyển vào `application-backend-server:8081/student`
  - Gọi `http://localhost/auth/` $\rightarrow$ Chuyển vào `authentication-identity-server:8080/`
- **Cân bằng tải Round Robin (Mở rộng 10):** Khi có quá đông người vào xem web, 1 máy chủ Web sẽ bị quá tải. Ta dựng 2 máy chủ Web giống hệt nhau (`web-frontend-server1` và `web-frontend-server2`). Thuật toán **Round Robin** (Xoay vòng) trên Nginx Proxy sẽ chia đều:
  - Khách thứ 1 vào $\rightarrow$ Giao cho **Server 1**
  - Khách thứ 2 vào $\rightarrow$ Giao cho **Server 2**
  - Khách thứ 3 vào $\rightarrow$ Quay lại **Server 1**...

### 4. Cơ chế bảo mật OIDC & JWT Bearer Token (Giữa Keycloak và Flask API)
Tại sao đường dẫn `/hello` ai gọi cũng được, còn `/secure` lại báo lỗi `401 Missing Bearer token`?
1. Người dùng gửi `username=sv01` & `password=123456` tới **Keycloak** (`realm_sv001`, client `flask-app`).
2. Keycloak kiểm tra đúng mật khẩu $\rightarrow$ Cấp cho người dùng 1 chuỗi mã hóa gọi là **JWT Access Token** (được ký bằng khóa bí mật **RS256** của Keycloak).
3. Người dùng cầm Token này đính vào đầu yêu cầu (`Authorization: Bearer <token>`) gửi tới `/api/secure` của **Flask Backend**.
4. **Flask Backend** hỏi Keycloak bộ khóa công khai (**JWKS**) để kiểm tra chữ ký trên Token. Nếu Token thật và chưa hết hạn $\rightarrow$ Cho phép vào và trả về `{"message": "Secure resource OK", "preferred_username": "sv01"}`.

---

## PHẦN 3: TÓM TẮT YÊU CẦU TÍNH ĐIỂM CỦA ĐỀ BÀI (Thang điểm 10/10)

Đề bài của thầy/cô chia làm **2 phần rõ rệt**, mỗi phần **5.0 điểm**:

### A. Phần Cơ Bản (5.0 điểm) — Dựng hệ thống 9 Server chạy đúng thiết kế
1. **Web Server (`:8080`):** Vào được trang chủ `/` và `/blog/` trả về `200 OK`.
2. **Backend Server (`:8085`):** Gọi `/hello` trực tiếp và qua `/api/hello` trả về JSON.
3. **Database Server (`:3306`):** Tự tạo CSDL `minicloud`, bảng `notes` có dòng `Hello from MariaDB!`.
4. **Keycloak Auth (`:8081`):** Mở được trang quản trị Keycloak, đăng nhập `admin/admin`.
5. **MinIO Storage (`:9001`):** Đăng nhập `minioadmin/minioadmin`, tạo bucket `demo`, tải lên `index.html`.
6. **Bind9 DNS (`:1053`):** Lệnh `dig` phân giải được `web-frontend-server.cloud.local` ra `10.10.10.10`.
7. **Prometheus (`:9090`):** Thu thập metric từ `monitoring-node-exporter-server:9100` báo trạng thái `UP`.
8. **Grafana (`:3000`):** Kết nối Prometheus và hiển thị biểu đồ giám sát.
9. **API Gateway Proxy (`:80`):** Gọi `/`, `/api/hello`, `/auth/` qua cổng 80 hoạt động đúng.
10. **Thông mạng (`ping`):** Các container trong mạng `cloud-net` ping thấy nhau 100%.

### B. Phần Mở Rộng – Ứng dụng thực tế (5.0 điểm = 10 mục $\times$ 0.5 điểm)
*(Mình đã làm trọn vẹn cả 10/10 mục này cho bạn)*:
1. **Web (`0.5đ`):** Tạo Blog cá nhân 3 bài viết (`blog1.html`, `blog2.html`, `blog3.html`) có ảnh minh họa và link ở `index.html`.
2. **Backend (`0.5đ`):** Tạo `students.json` (5 sinh viên) và API `/student` trả về danh sách JSON.
3. **Database (`0.5đ`):** Tạo CSDL `studentdb`, bảng `students` (chèn 5 sinh viên, truy vấn CRUD) và API `/api/students-db` đọc trực tiếp từ MariaDB.
4. **Keycloak (`0.5đ`):** Tạo Realm `realm_sv001`, Client `flask-app`, 2 user `sv01`/`sv02`, lấy Token gọi thành công vào `/secure`.
5. **MinIO (`0.5đ`):** Tạo bucket `profile-pics`, tải ảnh đại diện `avatar.png` & file PDF, mở quyền Public URL.
6. **DNS (`0.5đ`):** Thêm bản ghi `app-backend.cloud.local` (`10.10.10.20`), `minio.cloud.local` (`10.10.10.30`), `keycloak.cloud.local` (`10.10.10.40`).
7. **Prometheus (`0.5đ`):** Thêm job `'web'` giám sát `web-frontend-server:80` và đảm bảo target báo `UP`.
8. **Grafana (`0.5đ`):** Tạo Dashboard cá nhân `System Health of SV001` gồm 3 biểu đồ: *CPU Usage*, *Memory Usage*, *Network Traffic*.
9. **API Gateway (`0.5đ`):** Thêm route `/student/` trên Nginx Proxy trỏ thẳng vào API `/student` của Backend.
10. **Load Balancer (`0.5đ`):** Dựng 2 Web Server (`web-frontend-server1` & `web-frontend-server2`) và cấu hình cân bằng tải **Round Robin** trên Nginx Proxy.

---

## PHẦN 4: CÁC VIỆC BẠN CẦN LÀM ĐỂ NỘP BÀI & BẢO VỆ

### Việc 1: Hoàn thiện thông tin cá nhân trong Báo cáo Word (2 phút)
- Mở file [`Bai_Nop_Cuoi_Ky/Bao_Cao_Cuoi_Ky_MyMiniCloud.docx`](./Bao_Cao_Cuoi_Ky_MyMiniCloud.docx).
- Ở **Trang bìa (Trang 1)**, điền **Họ tên**, **MSSV**, **Lớp/Nhóm**, **Giảng viên hướng dẫn** vào các dòng dấu chấm `........`.
- Xem lướt qua 5 Chương của báo cáo để nắm bố cục (mọi sơ đồ, bảng biểu, code và ảnh kết quả kiểm thử đã có sẵn đầy đủ trong file Word).

### Việc 2: Nếu chỉ cần nộp file lên hệ thống (LMS / Drive / Classroom)
- Bạn lấy trực tiếp 2 file trong thư mục [`Bai_Nop_Cuoi_Ky/`](./):
  1. `Bao_Cao_Cuoi_Ky_MyMiniCloud.docx` (Báo cáo Word)
  2. `myminicloud_source_code.zip` (hoặc thư mục `myminicloud/` chứa toàn bộ code)

### Việc 3: Nếu thầy/cô yêu cầu bật chạy Demo trực tiếp trên máy hoặc quay Video
1. Bật phần mềm **Docker Desktop** trên máy tính của bạn (chấp nhận điều khoản *Accept* ở lần mở đầu tiên; nếu máy chưa bật WSL2 thì mở PowerShell quyền Admin gõ `wsl --install` rồi khởi động lại).
2. Khi Docker Desktop đã chạy, mở PowerShell gõ 2 dòng:
   ```powershell
   cd "D:\Dien toan dam may\baitapcuoiki\Bai_Nop_Cuoi_Ky\myminicloud"
   .\test_all.ps1
   ```
3. Kịch bản `test_all.ps1` sẽ tự động bật cả 11 containers, tự tạo dữ liệu và chạy kiểm thử toàn bộ 20 mục từ đầu đến cuối trên màn hình cho bạn quay video hoặc chụp ảnh!
4. Bạn có thể mở trình duyệt vào các địa chỉ sau để demo giao diện trực quan:
   - Trang chủ & Load Balancer: `http://localhost/`
   - Trang Blog 3 bài viết: `http://localhost:8080/blog/`
   - API Danh sách sinh viên (JSON): `http://localhost/student/`
   - API Danh sách sinh viên (từ MariaDB): `http://localhost/api/students-db`
   - Giao diện Keycloak Auth: `http://localhost:8081/` *(Tài khoản: `admin` / `admin`)*
   - Giao diện MinIO S3: `http://localhost:9001/` *(Tài khoản: `minioadmin` / `minioadmin`)*
   - Giao diện Prometheus Targets: `http://localhost:9090/targets`
   - Giao diện Grafana Dashboard: `http://localhost:3000/` *(Tài khoản: `admin` / `admin` -> vào Dashboards -> `System Health of SV001`)*

