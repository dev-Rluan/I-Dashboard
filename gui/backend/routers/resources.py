from fastapi import APIRouter
from core.resources import get_resources

router = APIRouter()


@router.get("/resources")
def get_system_resources():
    return get_resources()
