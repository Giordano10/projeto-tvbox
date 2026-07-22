#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

"$ROOT_DIR/.venv/bin/pip" install -r requirements.txt

mkdir -p content/biblioteca content/gerado config state logs

if [ ! -f state/dispositivos.json ]; then
  cat > state/dispositivos.json <<'EOF'
{
  "items": {}
}
EOF
fi

if [ ! -f config/dispositivos.json ]; then
  cat > config/dispositivos.json <<'EOF'
{
  "tv_saguao": {
    "screen_id": "tv_saguao",
    "label": "TV do Saguão",
    "ip": "192.168.15.16",
    "ativo": true,
    "device_token": "trocar-este-token",
    "aliases": ["tv do saguao", "saguao"]
  },
  "tv_sala": {
    "screen_id": "tv_sala",
    "label": "TV da Sala",
    "ip": "192.168.15.17",
    "ativo": true,
    "device_token": "trocar-este-token",
    "aliases": ["tv da sala", "sala"]
  },
  "tv_diretoria": {
    "screen_id": "tv_diretoria",
    "label": "TV da Diretoria",
    "ip": "192.168.15.18",
    "ativo": true,
    "device_token": "trocar-este-token",
    "aliases": ["tv da diretoria", "diretoria"]
  }
}
EOF
fi

if [ ! -f config/settings.yml ]; then
  cat > config/settings.yml <<'EOF'
porta: 8080
modo: local
polling_segundos: 5
flask_secret_key: desenvolvimento-tvb
picoclaw:
  habilitado: true
  bin: /home/admin/picoclaw_agent
  modelo: antigravity
  mensageiro: telegram
EOF
fi

echo "Instalacao base concluida. Execute: .venv/bin/python -m sinalizacao.server.app"
