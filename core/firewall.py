from core.platform import get_platform

_platform = get_platform()


def get_firewall_status() -> dict:
    """방화벽 상태 및 규칙을 반환한다.

    반환 형식:
        {"supported": bool, "engine": str, "active": bool,
         "rules": [{"direction": str, "action": str,
                    "protocol": str, "port": str, "source": str}]}
    """
    try:
        return _platform.get_firewall_status()
    except Exception:
        return {"supported": False, "engine": "unknown", "active": False, "rules": []}
