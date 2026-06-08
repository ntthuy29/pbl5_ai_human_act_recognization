from fastapi import APIRouter
from app.core.app_state import app_state
router = APIRouter()
@router.get("/latest")
@router.get("/lastest")
def get_lastest_data(): 
    app_state.refresh_connections()
    if not app_state.latest_prediction:
        return {
            "success": False,
            "message": "Chưa có dữ liệu"
        }
    return {
        "success": True,
        "data": {
            **app_state.latest_prediction,
            "is_live": app_state.monitoring,
        }
    }
