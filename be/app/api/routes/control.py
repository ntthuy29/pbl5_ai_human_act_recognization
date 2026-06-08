from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.hardware_service import hardware_service
router = APIRouter()
@router.post("/control/start")
def start_monitoring(user: User = Depends(get_current_user)):
    hardware_service.start(user_id=user.id)
    return {
        "success": True,
        "message": "Đã bắt đầu giám sát"
    }
@router.post("/control/stop")
def stop_monitoring(user: User = Depends(get_current_user)):
    hardware_service.stop()
    return {
        "success": True,
        "message": "Đã dừng giám sát"
    }
    