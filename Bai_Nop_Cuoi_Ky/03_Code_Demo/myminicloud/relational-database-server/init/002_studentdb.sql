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
  ('SAMPLE001', 'Sample Student 01', '2000-01-01', 'Cloud Computing'),
  ('SAMPLE002', 'Sample Student 02', '2000-01-02', 'Software Engineering'),
  ('SAMPLE003', 'Sample Student 03', '2000-01-03', 'Information Security'),
  ('SAMPLE004', 'Sample Student 04', '2000-01-04', 'Artificial Intelligence'),
  ('SAMPLE005', 'Sample Student 05', '2000-01-05', 'Information Systems'),
  ('SEEDTEST', 'Temporary Seed Row', '2000-01-31', 'Test');

-- Thực hành truy vấn cập nhật (UPDATE)
UPDATE students
SET major = 'Cloud and Distributed Systems'
WHERE student_id = 'SAMPLE001';

-- Thực hành truy vấn xóa (DELETE)
DELETE FROM students
WHERE student_id = 'SEEDTEST';

-- Thực hành truy vấn đọc (SELECT)
SELECT * FROM students;
