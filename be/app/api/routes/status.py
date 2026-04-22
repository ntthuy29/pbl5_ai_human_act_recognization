from fastapi import APIRouter

from app.core.app_state import app_state
from app.services.model_service import model_service

router = APIRouter()

@router.get("/status")
def get_status():
    app_state.refresh_connections()
    return {
        "success": True,
        "data": {
            "backend": "running",
            "model_loaded": app_state.model_loaded,
            "feature_dim": model_service.feature_dim,
            "esp32_1_connected": app_state.esp32_1_connected,
            "esp32_2_connected": app_state.esp32_2_connected,
            "monitoring": app_state.monitoring,
        }
    }