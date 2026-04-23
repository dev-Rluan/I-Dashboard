# I-Dashboard

서버 인프라 상태를 실시간으로 시각화하는 대시보드.  
**CLI(TUI)** 와 **GUI(웹)** 두 가지 방식으로 실행 가능하며, Linux / Windows / macOS를 모두 지원합니다.

---

## 지원 환경

| 기능 | Linux | Windows | macOS |
|------|:-----:|:-------:|:-----:|
| 포트 스캐너 | ✅ | ✅ | ✅ |
| 방화벽 상태 | ✅ (ufw/iptables/firewalld) | ✅ (Defender) | ✅ (pf) |
| CPU / 메모리 / 디스크 | ✅ | ✅ | ✅ |
| 네트워크 인터페이스 | ✅ | ✅ | ✅ |
| 프로세스 모니터 | ✅ | ✅ | ✅ |
| 시스템 서비스 | ✅ (systemd) | ✅ (Windows Services) | ✅ (launchd) |
| 로그 뷰어 | ✅ (/var/log) | ✅ (Event Log) | ✅ (system.log) |
| 도커 컨테이너 | ✅ | ✅ | ✅ |

---

## 구조

```
I-Dashboard/
├── core/                  # 공통 데이터 수집 모듈 (크로스 플랫폼)
│   ├── platform/          # OS별 구현 추상화 레이어
│   ├── ports.py
│   ├── firewall.py
│   ├── resources.py
│   ├── network.py
│   ├── processes.py
│   ├── services.py
│   ├── logs.py
│   └── docker.py
│
├── cli/                   # TUI 버전 (rich 기반)
│   └── main.py
│
├── gui/                   # 웹 대시보드 버전
│   ├── backend/           # FastAPI
│   └── frontend/          # React + Vite
│
├── docker/                # Docker 이미지 파일
├── docker-compose.yml     # 프로덕션 배포
└── docker-compose.dev.yml # 개발 환경
```

---

## 실행 방법

### 방법 1 — Docker Compose (GUI, 권장)

```bash
git clone https://github.com/dev-Rluan/I-Dashboard.git
cd I-Dashboard

# 환경변수 설정 (선택 — 인증 활성화 시)
cp .env.example .env

docker-compose up -d
```

브라우저에서 `http://서버IP:3000` 접속.

> **Windows / macOS**: Docker Desktop 환경에서는 호스트 네트워크 마운트 제약으로 일부 기능이 제한될 수 있습니다.

### 방법 2 — CLI (TUI)

```bash
pip install -r requirements.txt
python cli/main.py
```

| 키 | 동작 |
|----|------|
| `1` ~ `7` | 섹션 전환 (포트 / 방화벽 / 리소스 / 네트워크 / 프로세스 / 서비스 / 도커) |
| `r` | 수동 새로고침 |
| `q` | 종료 |

> 방화벽 수집은 관리자 권한이 필요할 수 있습니다.  
> Linux/macOS: `sudo python cli/main.py`, Windows: 관리자 권한 터미널에서 실행

### 방법 3 — 직접 실행 (GUI 개발)

```bash
pip install -r requirements.txt

# 백엔드
uvicorn gui.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드
cd gui/frontend && npm install && npm run dev
```

---

## 환경변수 (.env)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DASHBOARD_USER` | (없음) | Basic Auth 사용자명 (설정 시 인증 활성화) |
| `DASHBOARD_PASS` | (없음) | Basic Auth 비밀번호 |
| `REFRESH_INTERVAL` | `5` | 자동 갱신 주기 (초) |
| `HOST_PROC` | `/proc` | Docker 내부에서 호스트 /proc 경로 |
| `HOST_SYS` | `/sys` | Docker 내부에서 호스트 /sys 경로 |

---

## 기능

| 기능 | CLI | GUI |
|------|:---:|:---:|
| 포트 스캐너 | ✅ | ✅ |
| 방화벽 상태 | ✅ | ✅ |
| CPU / 메모리 / 디스크 | ✅ | ✅ |
| 네트워크 인터페이스 | ✅ | ✅ |
| 프로세스 모니터 | ✅ | ✅ |
| 시스템 서비스 | ✅ | ✅ |
| 로그 뷰어 | ✅ | ✅ |
| 도커 컨테이너 | ✅ | ✅ |
| 실시간 WebSocket | ❌ | ✅ |
| 브라우저 알림 | ❌ | ✅ |

---

## 요구사항

### CLI
- Python 3.10+
- `pip install -r requirements.txt`

### GUI (직접 실행)
- Python 3.10+, Node.js 18+

### GUI (Docker)
- Docker 20.10+, Docker Compose v2+

---

## 보안

- `DASHBOARD_USER` / `DASHBOARD_PASS` 환경변수 설정 시 Basic Auth 활성화
- 읽기 전용 — 서버 제어 기능 없음
- Docker 소켓 마운트는 읽기 전용(`:ro`)
- HTTPS: Nginx 설정에서 self-signed 인증서 사용 가능
