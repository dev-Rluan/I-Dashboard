from fastapi import APIRouter
from core.ports import get_open_ports

router = APIRouter()


@router.get("/ports")
def list_ports():
    return get_open_ports()
