from fastapi import APIRouter
from app.core.app_state import app_state
router = APIRouter()
@router.get("/lastest")
def get_lastest_data(): 
    if not app_state.lastest_prediction:
        return {
            "success": False,
            "message": "No data available"
        }
    return {
        "success": True,
        "data": app_state.lastest_prediction
    }
