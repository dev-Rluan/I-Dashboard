import psutil


def get_processes() -> list[dict]:
    """실행 중인 프로세스 목록을 반환한다.

    반환 형식:
        [{"pid": int, "name": str, "status": str,
          "cpu_percent": float, "memory_percent": float,
          "memory_mb": float, "user": str, "cmdline": str}]
    """
    results = []
    attrs = ["pid", "name", "status", "cpu_percent", "memory_info",
             "memory_percent", "username", "cmdline"]

    try:
        for proc in psutil.process_iter(attrs):
            try:
                info = proc.info
                mem_mb = 0.0
                if info.get("memory_info"):
                    mem_mb = info["memory_info"].rss / 1024 / 1024

                cmdline = info.get("cmdline") or []
                cmdline_str = " ".join(cmdline)[:120] if cmdline else ""

                results.append({
                    "pid": info.get("pid", 0),
                    "name": info.get("name") or "",
                    "status": info.get("status") or "unknown",
                    "cpu_percent": info.get("cpu_percent") or 0.0,
                    "memory_percent": round(info.get("memory_percent") or 0.0, 2),
                    "memory_mb": round(mem_mb, 1),
                    "user": info.get("username") or "",
                    "cmdline": cmdline_str,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        return []

    return results
