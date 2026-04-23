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


class LinuxPlatform(AbstractPlatform):

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
            key = (laddr.port, conn.type.name.lower() if hasattr(conn.type, "name") else "tcp")
            if key in seen:
                continue
            seen.add(key)

            proto = "udp" if conn.type and "UDP" in str(conn.type).upper() else "tcp"
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
        empty = {"supported": False, "engine": "unknown", "active": False, "rules": []}

        # ufw 우선
        ufw_out = _run(["ufw", "status", "verbose"])
        if ufw_out:
            active = "Status: active" in ufw_out
            rules = _parse_ufw_rules(ufw_out)
            return {"supported": True, "engine": "ufw", "active": active, "rules": rules}

        # iptables fallback
        ipt_out = _run(["iptables", "-L", "-n", "--line-numbers"])
        if ipt_out:
            rules = _parse_iptables_rules(ipt_out)
            return {"supported": True, "engine": "iptables", "active": True, "rules": rules}

        # firewalld fallback
        fwd_out = _run(["firewall-cmd", "--state"])
        if fwd_out.strip() == "running":
            rules_out = _run(["firewall-cmd", "--list-all"])
            rules = _parse_firewalld_rules(rules_out)
            return {"supported": True, "engine": "firewalld", "active": True, "rules": rules}

        return empty

    def get_services(self) -> list[dict]:
        out = _run([
            "systemctl", "list-units", "--type=service",
            "--all", "--no-pager", "--plain", "--no-legend",
        ])
        if not out:
            return []

        services = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            name = parts[0].removesuffix(".service")
            load = parts[1]
            active = parts[2]
            sub = parts[3]
            description = " ".join(parts[4:]) if len(parts) > 4 else ""

            if load != "loaded":
                continue

            status = _map_systemd_status(active, sub)
            enabled = _get_enabled_status(name)

            services.append({
                "name": name,
                "status": status,
                "enabled": enabled,
                "description": description,
            })

        return sorted(services, key=lambda x: x["name"])

    def get_service_logs(self, service_name: str, lines: int = 20) -> list[str]:
        out = _run(["journalctl", "-u", service_name, f"-n{lines}", "--no-pager", "--output=short"], timeout=10)
        return [l for l in out.splitlines() if l.strip()]

    def get_logs(self, log_type: str = "system", lines: int = 100) -> list[dict]:
        log_files = {
            "system": ["/var/log/syslog", "/var/log/messages"],
            "auth": ["/var/log/auth.log", "/var/log/secure"],
        }
        paths = log_files.get(log_type, log_files["system"])

        for path in paths:
            try:
                out = _run(["tail", "-n", str(lines), path])
                if out:
                    return _parse_log_lines(out)
            except Exception:
                continue
        return []


def _parse_ufw_rules(output: str) -> list[dict]:
    rules = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("--") or ":" not in line and "/" not in line and "ALLOW" not in line and "DENY" not in line:
            continue
        action = "allow" if "ALLOW" in line.upper() else "deny" if "DENY" in line.upper() else "drop"
        direction = "inbound" if "IN" in line.upper() else "outbound" if "OUT" in line.upper() else "inbound"
        port_match = re.search(r"(\d+)(?:/(\w+))?", line)
        port = port_match.group(1) if port_match else "any"
        proto = port_match.group(2) if port_match and port_match.group(2) else "any"
        rules.append({"direction": direction, "action": action, "protocol": proto, "port": port, "source": "any"})
    return rules


def _parse_iptables_rules(output: str) -> list[dict]:
    rules = []
    direction = "inbound"
    for line in output.splitlines():
        if line.startswith("Chain INPUT"):
            direction = "inbound"
        elif line.startswith("Chain OUTPUT"):
            direction = "outbound"
        elif line.startswith("Chain FORWARD"):
            direction = "forward"

        parts = line.split()
        if len(parts) < 4 or not parts[0].isdigit():
            continue
        action_raw = parts[1].upper()
        action = "allow" if action_raw == "ACCEPT" else "drop" if action_raw == "DROP" else "deny"
        proto = parts[3] if len(parts) > 3 else "any"
        dpt_match = re.search(r"dpt:(\d+)", line)
        port = dpt_match.group(1) if dpt_match else "any"
        src_match = re.search(r"(\d+\.\d+\.\d+\.\d+(?:/\d+)?)", line)
        source = src_match.group(1) if src_match else "any"
        rules.append({"direction": direction, "action": action, "protocol": proto, "port": port, "source": source})
    return rules


def _parse_firewalld_rules(output: str) -> list[dict]:
    rules = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("services:"):
            for svc in line.replace("services:", "").split():
                rules.append({"direction": "inbound", "action": "allow", "protocol": "tcp", "port": svc, "source": "any"})
        elif line.startswith("ports:"):
            for p in line.replace("ports:", "").split():
                port, _, proto = p.partition("/")
                rules.append({"direction": "inbound", "action": "allow", "protocol": proto or "tcp", "port": port, "source": "any"})
    return rules


def _map_systemd_status(active: str, sub: str) -> str:
    if active == "active" and sub == "running":
        return "active"
    if active == "failed":
        return "failed"
    if active == "inactive":
        return "inactive"
    return active


def _get_enabled_status(name: str) -> bool:
    out = _run(["systemctl", "is-enabled", name])
    return out.strip() == "enabled"


def _parse_log_lines(output: str) -> list[dict]:
    entries = []
    for line in output.splitlines():
        if not line.strip():
            continue
        level = "INFO"
        upper = line.upper()
        if "ERROR" in upper or "CRIT" in upper or "EMERG" in upper:
            level = "ERROR"
        elif "WARN" in upper:
            level = "WARN"
        entries.append({"raw": line, "level": level})
    return entries
