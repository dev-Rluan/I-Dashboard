from core.platform import get_platform

_platform = get_platform()


def get_services() -> list[dict]:
    """시스템 서비스 목록을 반환한다.

    반환 형식:
        [{"name": str, "status": str, "enabled": bool, "description": str}]

    status 값: "active" | "inactive" | "failed" | "running" | "stopped" | "unknown"
    """
    try:
        return _platform.get_services()
    except Exception:
        return []


def get_service_logs(service_name: str, lines: int = 20) -> list[str]:
    """서비스 최근 로그를 반환한다. 실패 시 빈 리스트."""
    try:
        return _platform.get_service_logs(service_name, lines)
    except Exception:
        return []
