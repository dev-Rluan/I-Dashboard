import json
import subprocess


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return ""


def _docker_available() -> bool:
    return bool(_run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=3).strip())


def get_containers() -> dict:
    """실행 중인 도커 컨테이너 목록과 리소스를 반환한다.

    반환 형식:
        {"supported": bool, "containers": [
          {"id": str, "name": str, "image": str, "status": str,
           "cpu_percent": float, "memory_mb": float, "ports": str}
        ]}
    """
    if not _docker_available():
        return {"supported": False, "containers": []}

    # 컨테이너 목록
    ps_out = _run([
        "docker", "ps", "--format",
        '{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}",'
        '"status":"{{.Status}}","ports":"{{.Ports}}"}',
    ])
    if not ps_out:
        return {"supported": True, "containers": []}

    containers = []
    for line in ps_out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            c = json.loads(line)
            c["cpu_percent"] = 0.0
            c["memory_mb"] = 0.0
            containers.append(c)
        except json.JSONDecodeError:
            continue

    # stats 수집
    if containers:
        stats_out = _run([
            "docker", "stats", "--no-stream", "--format",
            '{"id":"{{.ID}}","cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}"}',
        ], timeout=15)
        stats_map: dict[str, dict] = {}
        for line in stats_out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                s = json.loads(line)
                stats_map[s["id"][:12]] = s
            except (json.JSONDecodeError, KeyError):
                continue

        for c in containers:
            stat = stats_map.get(c["id"][:12], {})
            if stat:
                cpu_str = stat.get("cpu", "0%").rstrip("%")
                try:
                    c["cpu_percent"] = float(cpu_str)
                except ValueError:
                    pass
                mem_str = stat.get("mem", "0B / 0B").split("/")[0].strip()
                c["memory_mb"] = _parse_mem(mem_str)

    return {"supported": True, "containers": containers}


def get_container_logs(container_id: str, lines: int = 50) -> list[str]:
    out = _run(["docker", "logs", "--tail", str(lines), container_id], timeout=10)
    return [l for l in out.splitlines() if l.strip()]


def _parse_mem(s: str) -> float:
    s = s.strip()
    try:
        if s.endswith("GiB"):
            return float(s[:-3]) * 1024
        if s.endswith("MiB"):
            return float(s[:-3])
        if s.endswith("KiB"):
            return float(s[:-3]) / 1024
        if s.endswith("GB"):
            return float(s[:-2]) * 1024
        if s.endswith("MB"):
            return float(s[:-2])
        if s.endswith("KB"):
            return float(s[:-2]) / 1024
        return float(s.rstrip("B")) / 1024 / 1024
    except ValueError:
        return 0.0
