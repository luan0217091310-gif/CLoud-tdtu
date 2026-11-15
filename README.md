# MyMiniCloud

Đồ án cuối kỳ học phần Điện toán đám mây (504087), Khoa Công nghệ Thông tin, Trường Đại học Tôn Đức Thắng.

| Thành phần | Thư mục |
|---|---|
| Báo cáo Word theo mẫu khoa | [01_Bao_Cao](Bai_Nop_Cuoi_Ky/01_Bao_Cao/) |
| PowerPoint trình bày báo cáo và demo | [02_Slide](Bai_Nop_Cuoi_Ky/02_Slide/) |
| Mã demo Docker Compose và hướng dẫn chạy | [03_Code_Demo](Bai_Nop_Cuoi_Ky/03_Code_Demo/myminicloud/) |

## Hoàn thiện hồ sơ

1. Điền họ tên và MSSV trên hai bìa Word, thông tin ký xác nhận và slide đầu. Chạy `python setup_demo.py --student-id MA_SINH_VIEN` trong thư mục mã demo để tạo realm và dashboard theo MSSV của nhóm. Mặc định dùng mã mẫu `DEMO0000`.
2. Chép ảnh `avatar.jpg` thật vào `03_Code_Demo/myminicloud/object-storage-server/sample-files/`. Xuất lại `bao-cao.pdf` sau khi sửa Word để demo MinIO sử dụng bản mới.
3. Chạy bộ kiểm thử theo hướng dẫn mã demo. Dùng log và ảnh chụp của lần chạy thật để điền Chapter 4 và Appendix C.
4. Điền địa chỉ EC2 sau khi kiểm tra từ bên ngoài, link Docker Hub sau khi push và link video demo. Trong Word, nhấn chuột phải vào mục lục rồi chọn **Update Field → Update entire table** sau khi chèn ảnh.

Có thể chỉnh trực tiếp Word và PowerPoint. Để tạo lại bản báo cáo gốc từ mã, dùng `python report/build_report.py` với `python-docx` và Graphviz. Script sinh báo cáo mới, vì vậy hãy dùng `--output` nếu muốn giữ bản đã chỉnh sửa.
