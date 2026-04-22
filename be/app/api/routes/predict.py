from fastapi import APIRouter, HTTPException

from app.schemas.predict_schema import PredictRequest, PredictResponse
from app.services.prediction_service import prediction_service

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
	try:
		prediction = prediction_service.predict_window(payload.window)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	return {
		"success": True,
		"data": prediction,
	}
