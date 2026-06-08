from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.predict_schema import PredictRequest, PredictResponse
from app.services.prediction_service import prediction_service

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, user: User = Depends(get_current_user)):
	try:
		prediction = prediction_service.predict_window(payload.window, user_id=user.id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	return {
		"success": True,
		"data": prediction,
	}
