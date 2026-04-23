# I-Dashboard

서버 인프라 상태를 실시간으로 시각화하는 대시보드.  
**CLI(TUI)** 와 **GUI(웹)** 두 가지 방식으로 실행 가능하며, 데이터 수집은 공통 `core/` 모듈을 공유합니다.

---

## 구조

```
I-Dashboard/
├── core/              # 공통 데이터 수집 모듈
│   ├── ports.py       # 포트 스캔
│   ├── firewall.py    # 방화벽 상태
│   ├── resources.py   # CPU / 메모리 / 디스크
│   ├── network.py     # 네트워크 인터페이스
│   ├── processes.py   # 프로세스 목록
│   ├── services.py    # systemd 서비스
│   └── docker.py      # 도커 컨테이너 (선택)
│
├── cli/               # TUI 버전 (rich 기반)
│   └── main.py
│
├── gui/               # 웹 대시보드 버전
│   ├── backend/       # FastAPI
│   └── frontend/      # React + Vite
│
└── docs/              # 기획서 / 작업계획
```

---

## 요구사항

- Python 3.10+
- Node.js 18+ (GUI 프론트엔드)
- Linux (Ubuntu / Debian / RHEL 계열)
- 방화벽 수집 시 `sudo` 권한 필요

---

## 설치

```bash
git clone https://github.com/dev-Rluan/I-Dashboard.git
cd I-Dashboard
pip install -r requirements.txt
```

---

## 실행

### CLI (TUI)

```bash
python cli/main.py
```

| 키 | 동작 |
|----|------|
| `1~7` | 섹션 전환 (포트 / 방화벽 / 리소스 / 네트워크 / 프로세스 / 서비스 / 도커) |
| `r` | 수동 새로고침 |
| `q` | 종료 |

### GUI (웹)

```bash
# 백엔드
uvicorn gui.backend.main:app --host 0.0.0.0 --port 8000

# 프론트엔드 (개발)
cd gui/frontend && npm install && npm run dev

# 프론트엔드 (프로덕션 빌드)
cd gui/frontend && npm run build
```

브라우저에서 `http://서버IP:8000` 접속.

### Docker Compose (GUI 프로덕션)

```bash
docker-compose up -d
```

---

## 기능

| 기능 | CLI | GUI |
|------|:---:|:---:|
| 포트 스캐너 | ✅ | ✅ |
| 방화벽 상태 | ✅ | ✅ |
| CPU / 메모리 / 디스크 | ✅ | ✅ |
| 네트워크 인터페이스 | ✅ | ✅ |
| 프로세스 모니터 | ✅ | ✅ |
| systemd 서비스 | ✅ | ✅ |
| 로그 뷰어 | ✅ | ✅ |
| 도커 컨테이너 | ✅ | ✅ |
| 실시간 WebSocket | ❌ | ✅ |
| 브라우저 알림 | ❌ | ✅ |

---

## 지원 방화벽

- `ufw` (Ubuntu 기본)
- `iptables`
- `firewalld` (RHEL / CentOS)

자동 감지 후 해당 방식으로 파싱합니다.

---

## 보안

- GUI는 환경변수로 Basic Auth 활성화 가능 (`DASHBOARD_USER`, `DASHBOARD_PASS`)
- 읽기 전용 — 서버 제어 기능 없음
- HTTPS 설정 권장

```bash
export DASHBOARD_USER=admin
export DASHBOARD_PASS=yourpassword
uvicorn gui.backend.main:app --host 0.0.0.0 --port 8000
```
