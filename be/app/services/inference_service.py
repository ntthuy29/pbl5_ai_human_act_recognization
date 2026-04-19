from collections import deque
import os

import numpy as np

from app.core.app_state import app_state
from app.services.history_service import history_service
from app.services.model_service import model_service
from app.services.preprocess_service import preprocess_service


class InferenceService:
    def __init__(
        self,
        window_size: int = 128,
        step_size: int = 64,
        feature_dim: int = 30,
    ):
        self.window_size = window_size
        self.step_size = step_size
        self.feature_dim = feature_dim

        self.buffer = deque(maxlen=window_size)
        self._samples_since_last_prediction = 0

    def handle_new_sample(self, sample):
        arr = np.asarray(sample, dtype=np.float32).reshape(-1)
        if arr.size != self.feature_dim:
            return None

        self.buffer.append(arr.tolist())
        self._samples_since_last_prediction += 1

        if len(self.buffer) < self.window_size:
            return None

        if self._samples_since_last_prediction < self.step_size:
            return None

        window = np.asarray(self.buffer, dtype=np.float32)
        processed = preprocess_service.process(window)
        prediction = model_service.predict(processed)

        self._samples_since_last_prediction = 0
        app_state.latest_prediction = prediction
        app_state.model_loaded = True
        history_service.add(prediction)

        return prediction


inference_service = InferenceService(
    window_size=int(os.getenv("WINDOW_SIZE", "128")),
    step_size=int(os.getenv("STEP_SIZE", "64")),
    feature_dim=int(os.getenv("FEATURE_DIM", "30")),
)