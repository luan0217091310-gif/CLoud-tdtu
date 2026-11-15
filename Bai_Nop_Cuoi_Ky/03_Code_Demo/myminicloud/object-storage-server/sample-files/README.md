# Tệp dùng cho bài demo MinIO

- Chép ảnh đại diện JPG của thành viên nhóm vào `avatar.jpg`. Chính sách đọc công khai chỉ áp dụng cho đối tượng này trên MinIO đang chạy.
- `bao-cao.pdf` được xuất từ báo cáo Word. Sau khi nhóm cập nhật Word, xuất lại PDF và thay tệp này.
- `demo/index.html` lấy trực tiếp từ mã nguồn web.

Tại thư mục `myminicloud`, chạy `docker compose run --rm -T object-storage-client` sau khi MinIO sẵn sàng. Sau đó dùng `curl -I http://localhost:9000/profile-pics/avatar.jpg` để kiểm tra HTTP 200.
