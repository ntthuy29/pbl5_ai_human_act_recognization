from datetime import datetime, timezone

import numpy as np

from app.core.app_state import app_state
from app.services.history_service import history_service
from app.services.model_service import model_service
from app.services.preprocess_service import preprocess_service
from app.services.amp_phase import prepare_model_feature_window
from app.websocket.prediction_ws import notify_latest_prediction


class PredictionService:
	def predict_window(self, window, user_id: int | None = None):
		arr = np.asarray(window, dtype=np.float32)

		if arr.ndim != 2:
			raise ValueError(f"window must be 2D, got shape={arr.shape}")

		arr = prepare_model_feature_window(arr, target_feature_dim=model_service.feature_dim)

		processed = preprocess_service.process(
			arr,
			model_type=model_service.model_type,
			target_feature_dim=model_service.feature_dim,
		)
		prediction = model_service.predict(processed)
		prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
		if "probability" in prediction and "probabilities" not in prediction:
			prediction["probabilities"] = prediction["probability"]

		print(
			"[PREDICTION] "
			f"presence={prediction.get('presence')} "
			f"raw_presence={prediction.get('raw_presence')} "
			f"confidence={(float(prediction.get('confidence', 0.0)) * 100):.1f}% "
			f"timestamp={prediction['timestamp']}"
		)

		app_state.latest_prediction = prediction
		app_state.model_loaded = True
		history_service.add(
			prediction,
			user_id=user_id,
			session_id=app_state.active_session_id,
		)
		notify_latest_prediction()

		return prediction


prediction_service = PredictionService()
