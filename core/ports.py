from core.platform import get_platform

_platform = get_platform()


def get_open_ports() -> list[dict]:
    """현재 LISTEN 중인 포트 목록을 반환한다.

    반환 형식:
        [{"port": int, "protocol": str, "state": str, "service": str,
          "pid": int, "process": str, "user": str}, ...]
    """
    try:
        return _platform.get_open_ports()
    except Exception:
        return []
