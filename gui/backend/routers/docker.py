from fastapi import APIRouter

router = APIRouter()


@router.get("/docker")
def get_docker():
    try:
        from core.docker import get_containers
        return get_containers()
    except ImportError:
        return {"supported": False, "containers": []}
