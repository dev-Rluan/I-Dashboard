# CLAUDE.md

## 프로젝트 개요

서버 인프라 모니터링 대시보드. CLI(TUI)와 GUI(웹) 두 버전을 제공하며, Linux / Windows / macOS를 모두 지원한다.  
데이터 수집은 `core/` 모듈이 담당하고, CLI/GUI가 공유한다.

## 디렉토리 구조

```
core/
  platform/     # OS별 구현 추상화 레이어 — 이 안에서만 OS 분기
  ports.py      # core/platform/ 주입받아 OS 무관하게 동작
  firewall.py
  resources.py  # psutil 기반 — 크로스 플랫폼, platform/ 불필요
  network.py    # psutil 기반
  processes.py  # psutil 기반
  services.py   # OS별 서비스 관리자 추상화 필요
  logs.py       # OS별 로그 경로/명령어 추상화 필요
  docker.py     # Docker CLI — 크로스 플랫폼

cli/
  main.py       # rich 기반 TUI, core/ import

gui/
  backend/      # FastAPI, core/ import해서 API/WebSocket 노출
  frontend/     # React + Vite + TypeScript + Tailwind + Recharts

docker/
  Dockerfile.backend
  Dockerfile.frontend
  nginx.conf

docker-compose.yml      # 프로덕션
docker-compose.dev.yml  # 개발
```

## 크로스 플랫폼 규칙

### OS 분기는 core/platform/ 안에서만

```python
# 올바른 방법 — platform/ 레이어 사용
from core.platform import get_platform
platform = get_platform()
ports = platform.get_open_ports()

# 금지 — core/*.py 안에서 직접 분기
import platform
if platform.system() == "Linux": ...   # ❌
```

### 지원 안 되는 기능은 빈 결과 반환

```python
# 올바른 방법
def get_firewall_rules():
    try:
        return _parse_rules()
    except (FileNotFoundError, PermissionError, NotImplementedError):
        return {"supported": False, "rules": []}

# 금지 — 예외 전파로 앱 중단
def get_firewall_rules():
    return _parse_rules()   # ❌ 예외 처리 없음
```

### subprocess 호출 시 필수 사항

```python
subprocess.run(
    ["ss", "-tuln"],
    capture_output=True,
    text=True,
    timeout=5,          # 반드시 timeout 지정
    check=False         # 실패해도 예외 발생 안 하도록
)
```

## core/ 모듈 작성 규칙

- 렌더링 / 출력 코드 절대 포함 금지 (print, rich 등)
- 각 함수는 `dict` 또는 `dataclass`를 반환
- `subprocess` 호출 시 `timeout` 반드시 지정
- 권한 없음 / 명령 없음 / 미지원 OS 모두 빈 결과 반환 (예외 전파 금지)
- `psutil` 기반 기능(resources, network, processes)은 platform/ 불필요

## Docker 규칙

### 호스트 정보 수집을 위한 마운트 (linux)

```yaml
volumes:
  - /proc:/host/proc:ro
  - /sys:/host/sys:ro
  - /var/run/docker.sock:/var/run/docker.sock:ro
network_mode: host
```

- Docker Desktop(Windows/macOS)에서는 호스트 마운트 제약 존재 → 제한된 기능 안내
- Docker 소켓은 항상 `:ro` (읽기 전용)
- 환경변수 `HOST_PROC`, `HOST_SYS`로 경로 주입 (기본값: `/proc`, `/sys`)

### Dockerfile 원칙

- 멀티 스테이지 빌드 사용 (빌드 이미지 ≠ 런타임 이미지)
- `root` 유저 실행 금지 — 전용 비권한 유저 생성
- 레이어 캐시 최적화: 의존성 설치 → 소스 복사 순서

## CLI (cli/) 작성 규칙

- `rich` 라이브러리만 사용 (curses 사용 금지)
- 자동 갱신: `rich.Live` + `threading.Event` 조합
- 키 입력: 별도 스레드에서 처리
- Windows 터미널 호환성 확인 (`rich`는 Windows Console 지원)

## GUI Backend (gui/backend/) 작성 규칙

- FastAPI 라우터는 기능별로 분리 (`routers/` 디렉토리)
- WebSocket 엔드포인트는 `routers/ws.py`로 분리
- 응답 스키마는 `schemas/` 디렉토리에 Pydantic 모델로 정의
- 인증 미들웨어: `DASHBOARD_USER` / `DASHBOARD_PASS` 환경변수 미설정 시 비활성화

## GUI Frontend (gui/frontend/) 작성 규칙

- TypeScript 사용 (`.ts`, `.tsx`)
- 다크모드 기본 (`dark` 클래스 전략, Tailwind)
- API 호출은 `lib/api.ts` 에서만 수행
- WebSocket 연결은 `hooks/useWebSocket.ts` 커스텀 훅 사용
- OS / 환경 정보는 `hooks/useSystemInfo.ts` 로 관리
- 미지원 기능은 `<UnsupportedFeature />` 컴포넌트로 표시

## 실행 명령어

```bash
# CLI 실행 (관리자 권한 필요 시)
python cli/main.py
sudo python cli/main.py        # Linux/macOS 방화벽 수집 시

# GUI 백엔드
uvicorn gui.backend.main:app --host 0.0.0.0 --port 8000 --reload

# GUI 프론트엔드 개발 서버
cd gui/frontend && npm run dev

# Docker (프로덕션)
docker-compose up -d

# Docker (개발)
docker-compose -f docker-compose.dev.yml up

# 의존성 설치
pip install -r requirements.txt
cd gui/frontend && npm install
```

## 작업 순서 (작업계획.md 기준)

1. **Phase 0**: 프로젝트 뼈대 + `core/platform/` 추상화 레이어 + Docker 뼈대
2. **Phase 1**: `core/ports.py` + `core/firewall.py` → `cli/` Phase 1
3. **Phase 2**: `core/resources.py` + `core/network.py` → CLI 확장
4. **Phase 3**: `core/processes.py` + `core/services.py` → CLI 완성
5. **Phase 4**: `gui/backend/` FastAPI API / WebSocket
6. **Phase 5**: `gui/frontend/` React 전체 페이지
7. **Phase 6**: `core/docker.py` + `core/logs.py` + 마무리

## 커밋 컨벤션

```
feat(범위): 설명
fix(범위): 설명
refactor(범위): 설명
docs: 설명
chore: 설명
```

범위: `core`, `core/platform`, `cli`, `gui/backend`, `gui/frontend`, `docker`

## 주의사항

- `core/` 함수는 반드시 권한 오류 / 명령 없음 / 미지원 OS를 처리해야 한다
- Docker 기능은 Docker 미설치 환경에서도 앱이 정상 동작해야 한다
- 포트 스캔은 기본적으로 현재 열린 포트만 조회 (전체 범위 스캔은 옵션)
- Windows에서 일부 `psutil` 기능은 관리자 권한 필요 — 명시적 안내
