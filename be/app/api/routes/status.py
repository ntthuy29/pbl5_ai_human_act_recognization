from fastapi import APIRouter

from app.core.app_state import app_state

router = APIRouter()

@router.get("/status")
def get_status():
    return {
        "success": True,
        "data": {
            "backend": "running",
            "model_loaded": app_state.model_loaded,
            "esp32_1_connected": app_state.esp32_1_connected,
            "esp32_2_connected": app_state.esp32_2_connected,
            "monitoring": app_state.monitoring,
        }
    }