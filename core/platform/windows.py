import re
import subprocess
import psutil

from .base import AbstractPlatform

WELL_KNOWN_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 465: "SMTPS",
    587: "SMTP/TLS", 993: "IMAPS", 995: "POP3S", 3306: "MySQL",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
    27017: "MongoDB", 5672: "RabbitMQ", 9200: "Elasticsearch",
    2181: "Zookeeper", 2375: "Docker", 2376: "Docker-TLS",
}


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            check=False, encoding="utf-8", errors="replace",
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return ""


class WindowsPlatform(AbstractPlatform):

    def get_open_ports(self) -> list[dict]:
        try:
            conns = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError):
            conns = []

        pid_map: dict[int, tuple[str, str]] = {}
        try:
            for proc in psutil.process_iter(["pid", "name", "username"]):
                pid_map[proc.pid] = (proc.info["name"] or "", proc.info["username"] or "")
        except Exception:
            pass

        seen: set[tuple[int, str]] = set()
        ports: list[dict] = []
        for conn in conns:
            if conn.status != psutil.CONN_LISTEN:
                continue
            laddr = conn.laddr
            if not laddr:
                continue
            proto = "udp" if conn.type and "UDP" in str(conn.type).upper() else "tcp"
            key = (laddr.port, proto)
            if key in seen:
                continue
            seen.add(key)

            pid = conn.pid or 0
            name, user = pid_map.get(pid, ("", ""))
            ports.append({
                "port": laddr.port,
                "protocol": proto,
                "state": "open",
                "service": WELL_KNOWN_PORTS.get(laddr.port, ""),
                "pid": pid,
                "process": name,
                "user": user,
            })

        return sorted(ports, key=lambda x: x["port"])

    def get_firewall_status(self) -> dict:
        state_out = _run(["netsh", "advfirewall", "show", "allprofiles", "state"])
        if not state_out:
            return {"supported": False, "engine": "unknown", "active": False, "rules": []}

        active = "ON" in state_out.upper()
        rules_out = _run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], timeout=10)
        rules = _parse_netsh_rules(rules_out) if rules_out else []
        return {"supported": True, "engine": "netsh", "active": active, "rules": rules}

    def get_services(self) -> list[dict]:
        out = _run(["sc", "query", "type=", "all", "state=", "all"], timeout=10)
        if not out:
            return []
        return _parse_sc_output(out)

    def get_service_logs(self, service_name: str, lines: int = 20) -> list[str]:
        query = f"*[System[Provider[@Name='{service_name}']]]"
        out = _run([
            "wevtutil", "qe", "Application",
            f"/q:{query}", f"/c:{lines}", "/rd:true", "/f:text",
        ], timeout=10)
        return [l for l in out.splitlines() if l.strip()]

    def get_logs(self, log_type: str = "system", lines: int = 100) -> list[dict]:
        channel_map = {"system": "System", "auth": "Security"}
        channel = channel_map.get(log_type, "System")
        out = _run([
            "wevtutil", "qe", channel,
            f"/c:{lines}", "/rd:true", "/f:text",
        ], timeout=15)
        if not out:
            return []
        return _parse_log_lines(out)


def _parse_netsh_rules(output: str) -> list[dict]:
    rules = []
    current: dict = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Rule Name:"):
            if current:
                rules.append(current)
            current = {}
        elif ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key == "direction":
                current["direction"] = "inbound" if "in" in val.lower() else "outbound"
            elif key == "action":
                current["action"] = "allow" if "allow" in val.lower() else "deny"
            elif key == "protocol":
                current["protocol"] = val.lower()
            elif key == "localport":
                current["port"] = val
            elif key == "remoteip":
                current["source"] = val

    if current:
        rules.append(current)

    normalized = []
    for r in rules:
        normalized.append({
            "direction": r.get("direction", "inbound"),
            "action": r.get("action", "allow"),
            "protocol": r.get("protocol", "any"),
            "port": r.get("port", "any"),
            "source": r.get("source", "any"),
        })
    return normalized


def _parse_sc_output(output: str) -> list[dict]:
    services = []
    current: dict = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SERVICE_NAME:"):
            if current.get("name"):
                services.append(current)
            current = {"name": line.split(":", 1)[1].strip(), "status": "stopped", "enabled": True, "description": ""}
        elif "STATE" in line:
            if "RUNNING" in line:
                current["status"] = "active"
            elif "STOPPED" in line:
                current["status"] = "inactive"
            elif "FAILED" in line:
                current["status"] = "failed"
        elif line.startswith("DISPLAY_NAME:"):
            current["description"] = line.split(":", 1)[1].strip()
    if current.get("name"):
        services.append(current)
    return sorted(services, key=lambda x: x["name"])


def _parse_log_lines(output: str) -> list[dict]:
    entries = []
    for line in output.splitlines():
        if not line.strip():
            continue
        level = "INFO"
        upper = line.upper()
        if "ERROR" in upper or "CRITICAL" in upper:
            level = "ERROR"
        elif "WARNING" in upper or "WARN" in upper:
            level = "WARN"
        entries.append({"raw": line, "level": level})
    return entries
