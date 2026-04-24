import os
import platform
import socket
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()


def _is_docker() -> bool:
    return Path("/.dockerenv").exists()


@router.get("/info")
def get_system_info():
    docker = _is_docker()
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "is_docker": docker,
        "host_proc": os.getenv("HOST_PROC", "/proc"),
    }
