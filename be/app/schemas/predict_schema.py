from typing import Dict, List

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
	window: List[List[float]] = Field(
		...,
		description="CSI window with shape (time_steps, feature_dim)",
		min_length=1,
	)


class PredictData(BaseModel):
	presence: str
	confidence: float
	probability: Dict[str, float]


class PredictResponse(BaseModel):
	success: bool
	data: PredictData
