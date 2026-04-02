from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {
        "success": True,
        "data": {
            "backend": "running",
            "model_loaded": False,
            "esp32_1_connected": False,
            "esp32_2_connected": False,
            "monitoring": False
        }
    }