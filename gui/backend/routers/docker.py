from fastapi import APIRouter
from core.docker import get_containers, get_container_logs

router = APIRouter()


@router.get("/docker")
def api_docker():
    return get_containers()


@router.get("/docker/{container_id}/logs")
def api_container_logs(container_id: str, lines: int = 50):
    logs = get_container_logs(container_id, lines)
    return {"id": container_id, "lines": logs}
