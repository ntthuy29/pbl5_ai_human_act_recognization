from fastapi import APIRouter
from app.services.inference_service import inference_service

router = APIRouter()


@router.get("/force_predict")
def force_predict():
    try:
        pred = inference_service.predict_from_buffer()
        return {"success": True, "data": pred}
    except Exception as exc:
        return {"success": False, "message": str(exc)}
