import re
from collections import Counter
from core.platform import get_platform

_platform = get_platform()


def get_logs(log_type: str = "system", lines: int = 100) -> list[dict]:
    """시스템 로그를 반환한다.

    반환 형식:
        [{"raw": str, "level": str}]
    level: "INFO" | "WARN" | "ERROR"
    """
    try:
        return _platform.get_logs(log_type, lines)
    except Exception:
        return []


def detect_ssh_bruteforce(threshold: int = 5) -> list[dict]:
    """auth 로그에서 SSH 브루트포스 시도를 감지한다.

    반환 형식:
        [{"ip": str, "attempts": int, "level": str}]
    """
    try:
        entries = _platform.get_logs("auth", 500)
    except Exception:
        return []

    ip_counter: Counter = Counter()
    pattern = re.compile(r"Failed password.*from (\d+\.\d+\.\d+\.\d+)")
    for entry in entries:
        m = pattern.search(entry.get("raw", ""))
        if m:
            ip_counter[m.group(1)] += 1

    result = []
    for ip, count in ip_counter.most_common():
        if count >= threshold:
            result.append({
                "ip": ip,
                "attempts": count,
                "level": "ERROR" if count >= 20 else "WARN",
            })
    return result
