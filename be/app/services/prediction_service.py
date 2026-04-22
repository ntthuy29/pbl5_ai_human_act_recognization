from datetime import datetime, timezone

import numpy as np

from app.core.app_state import app_state
from app.services.history_service import history_service
from app.services.model_service import model_service
from app.services.preprocess_service import preprocess_service


class PredictionService:
	def predict_window(self, window):
		arr = np.asarray(window, dtype=np.float32)

		if arr.ndim != 2:
			raise ValueError(f"window must be 2D, got shape={arr.shape}")

		if arr.shape[1] != model_service.feature_dim:
			raise ValueError(
				f"feature_dim mismatch: expected {model_service.feature_dim}, got {arr.shape[1]}"
			)

		processed = preprocess_service.process(arr)
		prediction = model_service.predict(processed)
		prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
		if "probability" in prediction and "probabilities" not in prediction:
			prediction["probabilities"] = prediction["probability"]

		app_state.latest_prediction = prediction
		app_state.model_loaded = True
		history_service.add(prediction)

		return prediction


prediction_service = PredictionService()
