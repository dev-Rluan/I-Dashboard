#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] 가상환경 생성 중..."
    python3 -m venv "$VENV_DIR"
    echo "[setup] 의존성 설치 중..."
    "$VENV_DIR/bin/pip" install --quiet psutil python-dotenv
    echo "[setup] 완료"
fi

source "$VENV_DIR/bin/activate"

if [ -z "$BACKEND_URL" ] && [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

if [ -z "$BACKEND_URL" ]; then
    echo "오류: BACKEND_URL이 설정되지 않았습니다."
    echo "  방법 1: export BACKEND_URL=http://서버IP:8000"
    echo "  방법 2: .env 파일에 BACKEND_URL=http://서버IP:8000 추가"
    exit 1
fi

exec python agent/main.py "$@"
