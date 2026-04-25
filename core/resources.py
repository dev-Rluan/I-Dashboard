import os
import platform
import time
import psutil

_IS_MACOS = platform.system() == "Darwin"
_MACOS_DATA_VOLUME = os.getenv("MACOS_DATA_VOLUME", "/System/Volumes/Data")

_prev_disk_io: dict = {}
_prev_disk_time: float = 0.0


def get_resources() -> dict:
    """CPU / 메모리 / 스왑 / 디스크 정보를 반환한다.

    반환 형식:
        {
          "cpu": {"percent": float, "per_core": list[float], "count": int},
          "memory": {"total": int, "used": int, "available": int,
                     "cached": int, "percent": float},
          "swap": {"total": int, "used": int, "percent": float},
          "disks": [{"mountpoint": str, "device": str, "total": int,
                     "used": int, "free": int, "percent": float,
                     "read_bytes_sec": float, "write_bytes_sec": float}]
        }
    """
    global _prev_disk_io, _prev_disk_time

    try:
        cpu_pct = psutil.cpu_percent(interval=0.1)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        cpu_count = psutil.cpu_count(logical=True) or 1
    except Exception:
        cpu_pct, per_core, cpu_count = 0.0, [], 1

    try:
        vm = psutil.virtual_memory()
        mem = {
            "total": vm.total,
            "used": vm.used,
            "available": vm.available,
            "cached": getattr(vm, "cached", 0),
            "percent": vm.percent,
        }
    except Exception:
        mem = {"total": 0, "used": 0, "available": 0, "cached": 0, "percent": 0.0}

    try:
        sw = psutil.swap_memory()
        swap = {"total": sw.total, "used": sw.used, "percent": sw.percent}
    except Exception:
        swap = {"total": 0, "used": 0, "percent": 0.0}

    disks = _get_disks()

    return {
        "cpu": {"percent": cpu_pct, "per_core": per_core, "count": cpu_count},
        "memory": mem,
        "swap": swap,
        "disks": disks,
    }


def _get_disks() -> list[dict]:
    global _prev_disk_io, _prev_disk_time

    now = time.time()
    elapsed = now - _prev_disk_time if _prev_disk_time else 1.0

    try:
        current_io = psutil.disk_io_counters(perdisk=True) or {}
    except Exception:
        current_io = {}

    disks = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        return []

    for part in partitions:
        try:
            # macOS APFS: 시스템 볼륨(/) 대신 데이터 볼륨 사용량으로 대체
            usage_path = (
                _MACOS_DATA_VOLUME
                if _IS_MACOS and part.mountpoint == "/" and os.path.isdir(_MACOS_DATA_VOLUME)
                else part.mountpoint
            )
            usage = psutil.disk_usage(usage_path)
        except (PermissionError, OSError):
            continue

        device_key = part.device.replace("/dev/", "").replace("\\", "").replace(":", "")
        prev = _prev_disk_io.get(device_key, {})
        curr = current_io.get(device_key, None)

        read_sec = 0.0
        write_sec = 0.0
        if curr and prev and elapsed > 0:
            read_sec = max(0, (curr.read_bytes - prev.get("read_bytes", 0)) / elapsed)
            write_sec = max(0, (curr.write_bytes - prev.get("write_bytes", 0)) / elapsed)

        if curr:
            _prev_disk_io[device_key] = {
                "read_bytes": curr.read_bytes,
                "write_bytes": curr.write_bytes,
            }

        disks.append({
            "mountpoint": part.mountpoint,
            "device": part.device,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
            "read_bytes_sec": read_sec,
            "write_bytes_sec": write_sec,
        })

    _prev_disk_time = now
    return disks
