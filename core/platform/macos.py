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
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return ""


class MacOSPlatform(AbstractPlatform):

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
        # macOS Application Firewall 상태 확인
        fw_out = _run([
            "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"
        ])
        if fw_out:
            active = "enabled" in fw_out.lower()
            return {
                "supported": True,
                "engine": "appfirewall",
                "active": active,
                "rules": _get_appfw_rules(),
            }

        # pf 시도 (sudo 필요할 수 있음)
        pf_out = _run(["pfctl", "-s", "rules"])
        if pf_out:
            rules = _parse_pf_rules(pf_out)
            return {"supported": True, "engine": "pf", "active": True, "rules": rules}

        return {"supported": False, "engine": "unknown", "active": False, "rules": []}

    def get_services(self) -> list[dict]:
        out = _run(["launchctl", "list"], timeout=10)
        if not out:
            return []
        return _parse_launchctl(out)

    def get_service_logs(self, service_name: str, lines: int = 20) -> list[str]:
        out = _run([
            "log", "show", "--predicate",
            f'subsystem == "{service_name}" OR process == "{service_name}"',
            "--last", "10m", "--style", "syslog",
        ], timeout=15)
        lines_out = out.splitlines()
        return [l for l in lines_out[-lines:] if l.strip()]

    def get_logs(self, log_type: str = "system", lines: int = 100) -> list[dict]:
        # unified log 사용 (macOS 10.12+)
        predicate = "eventType == logEvent" if log_type == "auth" else ""
        cmd = ["log", "show", "--last", "1h", "--style", "syslog"]
        if predicate:
            cmd += ["--predicate", predicate]
        out = _run(cmd, timeout=20)
        if out:
            result = _parse_log_lines(out)
            return result[-lines:]

        # fallback: /var/log/system.log
        out = _run(["tail", "-n", str(lines), "/var/log/system.log"])
        return _parse_log_lines(out) if out else []


def _get_appfw_rules() -> list[dict]:
    out = _run(["/usr/libexec/ApplicationFirewall/socketfilterfw", "--listapps"])
    rules = []
    for line in out.splitlines():
        if "ALLOW" in line.upper() or "BLOCK" in line.upper():
            action = "allow" if "ALLOW" in line.upper() else "deny"
            rules.append({
                "direction": "inbound",
                "action": action,
                "protocol": "any",
                "port": "any",
                "source": line.strip(),
            })
    return rules


def _parse_pf_rules(output: str) -> list[dict]:
    rules = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        action = "allow" if line.startswith("pass") else "deny" if line.startswith("block") else "allow"
        direction = "inbound" if " in " in line else "outbound" if " out " in line else "inbound"
        proto_match = re.search(r"\bproto\s+(\w+)", line)
        proto = proto_match.group(1) if proto_match else "any"
        port_match = re.search(r"port\s+(\d+)", line)
        port = port_match.group(1) if port_match else "any"
        rules.append({"direction": direction, "action": action, "protocol": proto, "port": port, "source": "any"})
    return rules


def _parse_launchctl(output: str) -> list[dict]:
    services = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        pid_str, exit_str, label = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not label or label == "Label":
            continue
        if pid_str != "-" and pid_str.isdigit():
            status = "active"
        elif exit_str != "0" and exit_str != "-":
            status = "failed"
        else:
            status = "inactive"
        services.append({
            "name": label,
            "status": status,
            "enabled": True,
            "description": "",
        })
    return sorted(services, key=lambda x: x["name"])


def _parse_log_lines(output: str) -> list[dict]:
    entries = []
    for line in output.splitlines():
        if not line.strip():
            continue
        level = "INFO"
        upper = line.upper()
        if "ERROR" in upper or "CRITICAL" in upper or "FAULT" in upper:
            level = "ERROR"
        elif "WARN" in upper:
            level = "WARN"
        entries.append({"raw": line, "level": level})
    return entries
