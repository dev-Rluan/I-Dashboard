import os
import psutil

# HOST_PROC가 /proc가 아닌 다른 경로로 설정된 경우 (Docker 컨테이너 내 호스트 proc 마운트)
# psutil이 해당 경로에서 프로세스/리소스 정보를 읽도록 리다이렉트
_host_proc = os.getenv("HOST_PROC", "")
if _host_proc and _host_proc != "/proc":
    psutil.PROCFS_PATH = _host_proc
