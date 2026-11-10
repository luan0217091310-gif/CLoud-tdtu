#!/usr/bin/env bash
# ==============================================================================
# KỊCH BẢN TỰ ĐỘNG CÀI ĐẶT DOCKER & TRIỂN KHAI MYMINICLOUD TRÊN AWS EC2 UBUNTU
# Chạy bằng lệnh: bash deploy_ec2.sh
# ==============================================================================
set -e

echo "=== [1/4] Cập nhật hệ thống Ubuntu EC2 và cài đặt các gói phụ thuộc ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg dnsutils iputils-ping python3

echo "=== [2/4] Cài đặt Docker Engine & Docker Compose Plugin ==="
if ! command -v docker &> /dev/null; then
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
fi

echo "=== [3/4] Khởi động dịch vụ Docker ==="
sudo systemctl enable docker
sudo systemctl start docker

echo "=== [4/4] Build và khởi chạy toàn bộ 9 Server MyMiniCloud ==="
cd "$(dirname "$0")"
sudo docker compose up -d --build
sudo docker compose ps

PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || hostname -I | awk '{print $1}')
echo "=================================================================="
echo " TRIỂN KHAI THÀNH CÔNG TRÊN AWS EC2! Địa chỉ IP Public: $PUBLIC_IP"
echo " - API Gateway / Web:  http://$PUBLIC_IP/"
echo " - Web Server 1:       http://$PUBLIC_IP:8080/"
echo " - Web Server 2:       http://$PUBLIC_IP:8082/"
echo " - Flask Backend API:  http://$PUBLIC_IP:8085/hello"
echo " - Keycloak Auth:      http://$PUBLIC_IP:8081/"
echo " - MinIO Console:      http://$PUBLIC_IP:9001/"
echo " - Prometheus UI:      http://$PUBLIC_IP:9090/"
echo " - Grafana Dashboard:  http://$PUBLIC_IP:3000/"
echo "=================================================================="

