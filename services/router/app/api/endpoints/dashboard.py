from fastapi import APIRouter, Depends
from app.services.observer import observer
from typing import Dict, Any

router = APIRouter()

@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get the current status of the Intelligent Burst Router and Lemonade System.
    """
    return observer.get_status()
