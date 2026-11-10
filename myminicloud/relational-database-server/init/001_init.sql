SET NAMES utf8mb4;

-- 1. Cơ sở dữ liệu mặc định (Phần cơ bản)
CREATE DATABASE IF NOT EXISTS minicloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE minicloud;

CREATE TABLE IF NOT EXISTS notes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO notes(title) VALUES ('Hello from MariaDB!');
INSERT INTO notes(title) VALUES ('MyMiniCloud Relational Database Server OK');

