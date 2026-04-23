from fastapi import APIRouter, Query
from core.processes import get_processes

router = APIRouter()


@router.get("/processes")
def list_processes(sort: str = Query("cpu", pattern="^(cpu|memory)$"), limit: int = Query(50, ge=1, le=500)):
    procs = get_processes()
    key = "cpu_percent" if sort == "cpu" else "memory_percent"
    procs = sorted(procs, key=lambda x: x.get(key, 0), reverse=True)
    return procs[:limit]
