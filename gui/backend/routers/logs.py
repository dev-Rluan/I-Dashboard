from fastapi import APIRouter, Query
from core.logs import get_logs, detect_ssh_bruteforce

router = APIRouter()


@router.get("/logs")
def api_get_logs(
    log_type: str = Query("system", pattern="^(system|auth)$"),
    lines: int = Query(100, ge=10, le=1000),
):
    return get_logs(log_type, lines)


@router.get("/logs/bruteforce")
def api_bruteforce(threshold: int = Query(5, ge=1, le=100)):
    return detect_ssh_bruteforce(threshold)
