#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/.agent.pid"
LOG_FILE="$SCRIPT_DIR/agent.log"

if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] 가상환경 생성 중..."
    python3 -m venv "$VENV_DIR"
    echo "[setup] 의존성 설치 중..."
    "$VENV_DIR/bin/pip" install --quiet psutil python-dotenv
    echo "[setup] 완료"
fi

PYTHON="$VENV_DIR/bin/python"

# .env 로드 (BACKEND_URL 미설정 시)
if [ -z "$BACKEND_URL" ] && [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        export "$line"
    done < "$SCRIPT_DIR/.env"
fi

if [ -z "$BACKEND_URL" ]; then
    echo "오류: BACKEND_URL이 설정되지 않았습니다."
    echo "  방법 1: export BACKEND_URL=http://서버IP:8000"
    echo "  방법 2: .env 파일에 BACKEND_URL=http://서버IP:8000 추가"
    exit 1
fi

case "${1:-}" in
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "에이전트 종료 (PID $PID)"
            else
                echo "이미 종료된 프로세스입니다."
                rm -f "$PID_FILE"
            fi
        else
            echo "실행 중인 에이전트가 없습니다."
        fi
        exit 0
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "실행 중 (PID $PID) — 로그: $LOG_FILE"
            else
                echo "종료됨 (PID 파일 잔존)"
                rm -f "$PID_FILE"
            fi
        else
            echo "실행 중인 에이전트가 없습니다."
        fi
        exit 0
        ;;
    log)
        tail -f "$LOG_FILE"
        exit 0
        ;;
    bg)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "이미 실행 중입니다. (PID $(cat "$PID_FILE"))"
            exit 1
        fi
        nohup "$PYTHON" agent/main.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "백그라운드 시작 (PID $!) — 로그: $LOG_FILE"
        exit 0
        ;;
esac

exec "$PYTHON" agent/main.py
