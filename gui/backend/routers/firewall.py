from fastapi import APIRouter
from core.firewall import get_firewall_status

router = APIRouter()


@router.get("/firewall")
def get_firewall():
    return get_firewall_status()
