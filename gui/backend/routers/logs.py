from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/logs")
def get_logs(log_type: str = Query("system", pattern="^(system|auth)$"), lines: int = Query(100, ge=10, le=1000)):
    try:
        from core.logs import get_logs as _get_logs
        return _get_logs(log_type, lines)
    except ImportError:
        return []
