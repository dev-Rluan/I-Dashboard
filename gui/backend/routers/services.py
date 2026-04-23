from fastapi import APIRouter, HTTPException
from core.services import get_services, get_service_logs

router = APIRouter()


@router.get("/services")
def list_services():
    return get_services()


@router.get("/services/{name}/logs")
def get_logs(name: str, lines: int = 20):
    logs = get_service_logs(name, lines)
    if logs is None:
        raise HTTPException(status_code=404, detail="Service not found or logs unavailable")
    return {"name": name, "lines": logs}
