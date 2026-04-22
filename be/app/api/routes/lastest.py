from fastapi import APIRouter
from app.core.app_state import app_state
router = APIRouter()
@router.get("/lastest")
def get_lastest_data(): 
    app_state.refresh_connections()
    if not app_state.monitoring or (not app_state.esp32_1_connected and not app_state.esp32_2_connected):
        return {
            "success": False,
            "message": "No live ESP32 data"
        }
    if not app_state.latest_prediction:
        return {
            "success": False,
            "message": "No data available"
        }
    return {
        "success": True,
        "data": app_state.latest_prediction
    }
