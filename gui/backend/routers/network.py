from fastapi import APIRouter
from core.network import get_network_interfaces

router = APIRouter()


@router.get("/network")
def get_network():
    return get_network_interfaces()
