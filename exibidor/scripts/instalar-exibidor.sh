#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
EXIBIDOR_ID="${EXIBIDOR_ID:-tv_saguao}"
GESTOR_BASE_URL="${GESTOR_BASE_URL:-http://gestor.local:8080}"
DEVICE_IP="${DEVICE_IP:-192.168.15.16}"
DEVICE_TOKEN="${DEVICE_TOKEN:-trocar-este-token}"

cd "$ROOT_DIR"

mkdir -p exibidor/cache exibidor/config

cat > exibidor/config/exibidor.conf <<EOF
exibidor_id=$EXIBIDOR_ID
gestor_base_url=$GESTOR_BASE_URL
device_ip=$DEVICE_IP
device_token=$DEVICE_TOKEN
cache_dir=exibidor/cache
polling_segundos=5
heartbeat_segundos=10
display_command=fbi
EOF

echo "Exibidor configurado em exibidor/config/exibidor.conf"
echo "Para executar: $PYTHON_BIN -m exibidor.main"
