SET NAMES utf8mb4;

-- 2. Cơ sở dữ liệu studentdb (Yêu cầu mở rộng 3)
CREATE DATABASE IF NOT EXISTS studentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_id VARCHAR(10),
  fullname VARCHAR(100),
  dob DATE,
  major VARCHAR(50)
);

-- Chèn dữ liệu mẫu (CREATE / INSERT)
INSERT INTO students (student_id, fullname, dob, major) VALUES
  ('SV001', 'Nguyễn Văn An', '2004-03-15', 'Điện toán đám mây'),
  ('SV002', 'Trần Thị Bình', '2004-07-22', 'Kỹ thuật phần mềm'),
  ('SV003', 'Lê Hoàng Cường', '2004-11-05', 'An toàn thông tin'),
  ('SV004', 'Phạm Minh Dung', '2004-01-19', 'Trí tuệ nhân tạo'),
  ('SV005', 'Hoàng Quốc Đạt', '2004-09-30', 'Hệ thống thông tin'),
  ('SV999', 'Bản ghi nháp tạm thời', '2004-12-31', 'Thử nghiệm');

-- Thực hành truy vấn cập nhật (UPDATE)
UPDATE students
SET major = 'Điện toán đám mây & Hệ phân tán'
WHERE student_id = 'SV001';

-- Thực hành truy vấn xóa (DELETE)
DELETE FROM students
WHERE student_id = 'SV999';

-- Thực hành truy vấn đọc (SELECT)
SELECT * FROM students;
