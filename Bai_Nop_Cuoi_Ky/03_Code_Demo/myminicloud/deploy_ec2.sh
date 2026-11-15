#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"

publish=0
case "${1:-}" in
  "") ;;
  --push) publish=1 ;;
  *) printf 'Usage: bash deploy_ec2.sh [--push]\n' >&2; exit 2 ;;
esac

if (( publish )); then
  : "${DOCKERHUB_USER:?Set DOCKERHUB_USER to your Docker Hub username.}"
fi

if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  . /etc/os-release
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl python3
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<DOCKER_SOURCE
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER_SOURCE
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
sudo systemctl enable --now docker
python3 setup_demo.py

if [[ -z "${PUBLIC_HOST:-}" ]]; then
  metadata_token=$(curl -fsS --max-time 3 -X PUT http://169.254.169.254/latest/api/token \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" || true)
  if [[ -n "$metadata_token" ]]; then
    PUBLIC_HOST=$(curl -fsS --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 \
      -H "X-aws-ec2-metadata-token: $metadata_token" || true)
  fi
fi
: "${PUBLIC_HOST:?Set PUBLIC_HOST to the public IPv4 address or DNS name of this EC2 instance.}"

docker_cmd=(docker)
if ! docker info >/dev/null 2>&1; then
  docker_cmd=(sudo docker)
fi

export GATEWAY_BIND_IP=0.0.0.0
export OIDC_PUBLIC_BASE_URL="http://$PUBLIC_HOST/auth"
if [[ "${docker_cmd[0]}" == sudo ]]; then
  docker_cmd=(sudo --preserve-env=GATEWAY_BIND_IP,OIDC_PUBLIC_BASE_URL,DB_HOST_PORT docker)
fi

"${docker_cmd[@]}" compose up -d --build --wait --wait-timeout 220
"${docker_cmd[@]}" compose ps
curl -fsS http://127.0.0.1/api/hello
printf '\nGateway demo: http://%s/\n' "$PUBLIC_HOST"

if (( publish )); then
  image="$DOCKERHUB_USER/myminicloud-web:demo"
  "${docker_cmd[@]}" login --username "$DOCKERHUB_USER"
  "${docker_cmd[@]}" tag myminicloud/web:demo "$image"
  "${docker_cmd[@]}" push "$image"
  printf 'Docker Hub: https://hub.docker.com/r/%s/myminicloud-web\n' "$DOCKERHUB_USER"
fi
