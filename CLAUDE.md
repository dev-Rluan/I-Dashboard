# CLAUDE.md

## 프로젝트 개요

서버 인프라 모니터링 대시보드. CLI(TUI)와 GUI(웹) 두 버전을 제공하며, 데이터 수집은 `core/` 모듈이 담당하고 CLI/GUI가 공유한다.

## 디렉토리 구조

```
core/       # 데이터 수집 전용 — 출력/렌더링 코드 없음, 순수 Python
cli/        # rich 기반 TUI, core/ import해서 사용
gui/
  backend/  # FastAPI, core/ import해서 API/WebSocket으로 노출
  frontend/ # React + Vite + Tailwind CSS + Recharts
docs/       # 기획서, 작업계획 (수정 시 함께 업데이트)
```

## 개발 규칙

### core/ 모듈
- 렌더링 / 출력 코드 절대 포함하지 않는다 (print, rich, logging 최소화)
- 각 함수는 dict 또는 dataclass를 반환한다
- subprocess 호출 시 `timeout` 반드시 지정
- 명령이 없거나 권한이 없을 때 예외 대신 빈 결과를 반환한다

### CLI (cli/)
- `rich` 라이브러리만 사용 (curses 사용 금지)
- 자동 갱신은 `Live` + `threading.Event` 조합 사용
- 키 입력은 별도 스레드에서 처리

### GUI Backend (gui/backend/)
- FastAPI 라우터는 기능별로 분리 (`routers/` 디렉토리)
- WebSocket 엔드포인트는 `ws/` 라우터로 분리
- 응답 스키마는 Pydantic 모델로 정의
- 인증 미들웨어는 환경변수 미설정 시 비활성화

### GUI Frontend (gui/frontend/)
- TypeScript 사용
- 다크모드 기본 (`dark` 클래스 전략, Tailwind)
- API 호출은 `lib/api.ts` 에서만 수행
- WebSocket 연결은 `hooks/useWebSocket.ts` 커스텀 훅 사용

## 실행 명령어

```bash
# CLI 실행
python cli/main.py

# GUI 백엔드 실행
uvicorn gui.backend.main:app --host 0.0.0.0 --port 8000 --reload

# GUI 프론트엔드 개발 서버
cd gui/frontend && npm run dev

# 의존성 설치
pip install -r requirements.txt
cd gui/frontend && npm install
```

## 의존성

### Python
- `psutil` — 시스템 리소스 수집
- `rich` — CLI TUI 렌더링
- `fastapi` — 웹 백엔드
- `uvicorn` — ASGI 서버
- `websockets` — WebSocket 지원

### Node.js
- `react`, `vite` — 프론트엔드 프레임워크
- `tailwindcss` — 스타일링
- `recharts` — 차트
- `react-router-dom` — 라우팅

## 작업 순서 (작업계획.md 기준)

1. **Phase 1**: `core/ports.py` → `core/firewall.py` → `cli/main.py` (포트/방화벽 TUI)
2. **Phase 2**: `core/resources.py` → `core/network.py` → CLI 확장
3. **Phase 3**: `core/processes.py` → `core/services.py` → CLI 완성
4. **Phase 4**: `gui/backend/` FastAPI API/WebSocket
5. **Phase 5**: `gui/frontend/` React 페이지
6. **Phase 6**: `core/docker.py` + 마무리

## 커밋 컨벤션

```
feat(범위): 설명
fix(범위): 설명
refactor(범위): 설명
docs: 설명
chore: 설명
```

범위 예시: `core`, `cli`, `gui/backend`, `gui/frontend`

## 주의사항

- `core/` 함수는 항상 권한 오류 / 명령 없음 케이스를 처리해야 한다
- 방화벽 관련 수집은 root 권한이 필요할 수 있으므로 graceful fallback 필수
- Docker 기능은 Docker 미설치 환경에서도 앱이 정상 동작해야 한다
- 포트 스캔 범위가 넓을 경우 성능에 주의 (기본은 well-known + 현재 열린 포트만 조회)
