from fastapi import APIRouter
from app.services.hardware_service import hardware_service
router = APIRouter()
@router.post("/control/start")
def start_monitoring():
    hardware_service.start()
    return {
        "success": True,
        "message": "Monitoring started"
    }
@router.post("/control/stop")
def stop_monitoring():
    hardware_service.stop()
    return {
        "success": True,
        "message": "Monitoring stopped"
    }
    