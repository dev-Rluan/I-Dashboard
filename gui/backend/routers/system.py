import platform
import socket
from fastapi import APIRouter

router = APIRouter()


@router.get("/info")
def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }
