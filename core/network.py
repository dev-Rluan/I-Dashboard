import time
import psutil

_prev_io: dict = {}
_prev_time: float = 0.0


def get_network_interfaces() -> list[dict]:
    """네트워크 인터페이스 목록 및 실시간 트래픽을 반환한다.

    반환 형식:
        [{"name": str, "ip": str, "mac": str, "status": str,
          "bytes_sent_sec": float, "bytes_recv_sec": float,
          "packets_err": int, "packets_drop": int}]
    """
    global _prev_io, _prev_time

    now = time.time()
    elapsed = now - _prev_time if _prev_time else 1.0

    try:
        addrs = psutil.net_if_addrs()
    except Exception:
        return []

    try:
        stats = psutil.net_if_stats()
    except Exception:
        stats = {}

    try:
        io_now = psutil.net_io_counters(pernic=True) or {}
    except Exception:
        io_now = {}

    interfaces = []
    for name, addr_list in addrs.items():
        ip = ""
        mac = ""
        for a in addr_list:
            if a.family.name in ("AF_INET",) and not ip:
                ip = a.address
            if a.family.name in ("AF_LINK", "AF_PACKET") and not mac:
                mac = a.address

        stat = stats.get(name)
        status = "up" if (stat and stat.isup) else "down"

        curr = io_now.get(name)
        prev = _prev_io.get(name, {})
        sent_sec = 0.0
        recv_sec = 0.0
        err = 0
        drop = 0
        if curr:
            if prev and elapsed > 0:
                sent_sec = max(0, (curr.bytes_sent - prev.get("bytes_sent", 0)) / elapsed)
                recv_sec = max(0, (curr.bytes_recv - prev.get("bytes_recv", 0)) / elapsed)
            err = getattr(curr, "errin", 0) + getattr(curr, "errout", 0)
            drop = getattr(curr, "dropin", 0) + getattr(curr, "dropout", 0)
            _prev_io[name] = {"bytes_sent": curr.bytes_sent, "bytes_recv": curr.bytes_recv}

        interfaces.append({
            "name": name,
            "ip": ip or "-",
            "mac": mac or "-",
            "status": status,
            "bytes_sent_sec": sent_sec,
            "bytes_recv_sec": recv_sec,
            "packets_err": err,
            "packets_drop": drop,
        })

    _prev_time = now
    return sorted(interfaces, key=lambda x: (x["status"] != "up", x["name"]))
