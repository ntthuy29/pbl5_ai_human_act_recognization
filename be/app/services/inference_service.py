from collections import deque
from datetime import datetime, timezone
import os
from pathlib import Path

import numpy as np

from app.core.app_state import app_state
from app.services.history_service import history_service
from app.services.model_service import model_service
from app.services.preprocess_service import (
    apply_global_normalizer,
    apply_standardizer,
    butterworth_lowpass,
    convert_window_to_spectrogram,
)
from app.websocket.prediction_ws import notify_latest_prediction


class InferenceService:
    def __init__(
        self,
        window_size: int = 128,
        step_size: int = 64,
        feature_dim: int = 192,
    ):
        self.window_size = int(window_size)
        self.step_size = int(step_size)
        self.feature_dim = int(feature_dim)

        self.buffer = deque(maxlen=self.window_size)
        self._samples_since_last_prediction = 0

        self.amp_mu_train: np.ndarray | None = None
        self.amp_sigma_train: np.ndarray | None = None
        self.amp_log = False
        self._load_amp_stats()
        self._log_preprocessing_config()

    def _load_amp_stats(self) -> None:
        configured_path = os.getenv("AMP_STATS_PATH")
        path = Path(configured_path) if configured_path else Path(__file__).with_name("amp_stats.npz")

        if not path.is_file():
            print(f"[INFERENCE] WARNING: amp stats not found: {path}")
            print("[INFERENCE] Realtime amplitude normalization will be skipped.")
            return

        stats = np.load(path)
        amp_mu = stats["amp_mu_train"].astype(np.float32).reshape(-1)
        amp_sigma = stats["amp_sigma_train"].astype(np.float32).reshape(-1)
        amp_log = bool(stats["amp_log"].item() if stats["amp_log"].shape == () else stats["amp_log"])

        expected_amp_dim = self.feature_dim // 3
        if expected_amp_dim > 0 and (amp_mu.size != expected_amp_dim or amp_sigma.size != expected_amp_dim):
            print(
                "[INFERENCE] WARNING: amp stats shape does not match model feature_dim. "
                f"amp_mu={amp_mu.size}, amp_sigma={amp_sigma.size}, expected={expected_amp_dim}"
            )
            return

        self.amp_mu_train = amp_mu
        self.amp_sigma_train = amp_sigma
        self.amp_log = amp_log

        print(
            f"[INFERENCE] Loaded amp stats: {path} "
            f"amp_dim={amp_mu.size} amp_log={self.amp_log}"
        )

    def _log_preprocessing_config(self) -> None:
        has_model_norm = (
            model_service.standardizer_mu is not None
            and model_service.standardizer_sigma is not None
            and model_service.global_max_abs is not None
        )
        model_norm_text = "Standardizer -> GlobalNorm" if has_model_norm else "no checkpoint normalizer"
        print(
            "[INFERENCE] Using train-like preprocessing: "
            "AmpStats -> PhaseEncoding -> ZScoreClip(threshold=5.0) -> "
            f"Butterworth(order=4, cutoff=0.1) -> Spectrogram(if cnn2d) -> {model_norm_text}"
        )

    def reset(self):
        self.buffer.clear()
        self._samples_since_last_prediction = 0

    def _prepare_feature_vector_like_train(self, sample) -> np.ndarray:
        arr = np.asarray(sample, dtype=np.float32).reshape(-1)

        if arr.size == self.feature_dim:
            return arr.astype(np.float32, copy=False)

        if arr.size == 0:
            return np.zeros(self.feature_dim, dtype=np.float32)

        if arr.size % 2 != 0:
            arr = np.pad(arr, (0, 1), mode="constant", constant_values=0.0)

        real = arr[0::2].astype(np.float32, copy=False)
        imag = arr[1::2].astype(np.float32, copy=False)

        amp = np.sqrt(real * real + imag * imag)
        if self.amp_log:
            amp = np.log(amp + 1e-8)

        if (
            self.amp_mu_train is not None
            and self.amp_sigma_train is not None
            and self.amp_mu_train.size == amp.size
            and self.amp_sigma_train.size == amp.size
        ):
            amp = (amp - self.amp_mu_train) / (self.amp_sigma_train + 1e-8)

        phase = np.arctan2(imag, real)
        encoded = np.concatenate((amp, np.cos(phase), np.sin(phase))).astype(
            np.float32,
            copy=False,
        )

        if encoded.size < self.feature_dim:
            encoded = np.pad(encoded, (0, self.feature_dim - encoded.size), mode="constant")
        elif encoded.size > self.feature_dim:
            encoded = encoded[: self.feature_dim]

        return encoded.astype(np.float32, copy=False)

    @staticmethod
    def _remove_outliers_zscore(x: np.ndarray, threshold: float = 5.0) -> np.ndarray:
        mu = np.mean(x, axis=0, keepdims=True)
        sigma = np.std(x, axis=0, keepdims=True) + 1e-8
        lower = mu - threshold * sigma
        upper = mu + threshold * sigma
        return np.clip(x, lower, upper).astype(np.float32)

    def _process_window_like_train(self, window) -> np.ndarray:
        arr = np.asarray(window, dtype=np.float32)

        arr = self._remove_outliers_zscore(arr, threshold=5.0)
        arr = butterworth_lowpass(arr, order=4, cutoff=0.1)

        if model_service.model_type.lower() == "cnn2d":
            arr = convert_window_to_spectrogram(
                arr,
                nperseg=model_service.spectrogram_nperseg,
            )

        if model_service.standardizer_mu is not None and model_service.standardizer_sigma is not None:
            arr = apply_standardizer(
                arr,
                model_service.standardizer_mu,
                model_service.standardizer_sigma,
            )

        if model_service.global_max_abs is not None:
            arr = apply_global_normalizer(arr, model_service.global_max_abs)

        return arr.astype(np.float32)

    def _publish_prediction(self, prediction: dict) -> dict:
        prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "probability" in prediction and "probabilities" not in prediction:
            prediction["probabilities"] = prediction["probability"]

        self._samples_since_last_prediction = 0
        app_state.latest_prediction = prediction
        app_state.model_loaded = True

        try:
            history_service.add(
                prediction,
                user_id=app_state.active_session_user_id,
                session_id=app_state.active_session_id,
            )
        except Exception as exc:
            print(f"[INFERENCE] Warning: history_service.add failed: {exc}")

        try:
            notify_latest_prediction()
        except Exception as exc:
            print(f"[INFERENCE] Warning: notify_latest_prediction failed: {exc}")

        return prediction

    def predict_from_buffer(self):
        """Run prediction on the current buffer if ready."""
        if len(self.buffer) < self.window_size:
            raise RuntimeError("Buffer not full")
        if self._samples_since_last_prediction < self.step_size:
            raise RuntimeError("Not enough new samples since last prediction")

        window = np.asarray(self.buffer, dtype=np.float32)
        processed = self._process_window_like_train(window)

        try:
            prediction = model_service.predict(processed)
        except Exception as exc:
            import traceback

            print(f"[INFERENCE DEBUG] Error during model.predict: {exc}")
            traceback.print_exc()
            raise

        return self._publish_prediction(prediction)

    def handle_new_sample(self, sample):
        arr = self._prepare_feature_vector_like_train(sample)
        if arr.size != self.feature_dim:
            return None

        self.buffer.append(arr.tolist())
        self._samples_since_last_prediction += 1

        try:
            buf_len = len(self.buffer)
            progress = 100.0 * buf_len / max(1, self.window_size)
            print(
                f"[BUFFER] len={buf_len}/{self.window_size} progress={progress:.1f}% "
                f"samples_since_last_prediction={self._samples_since_last_prediction}/{self.step_size}"
            )
        except Exception:
            pass

        if len(self.buffer) < self.window_size:
            return None

        if self._samples_since_last_prediction < self.step_size:
            return None

        window = np.asarray(self.buffer, dtype=np.float32)
        processed = self._process_window_like_train(window)

        print("[INFERENCE] === PREDICTION CYCLE ===")
        print(
            f"[INFERENCE] RAW window: shape={window.shape}, mean={window.mean():.6f}, "
            f"std={window.std():.6f}, min={window.min():.6f}, max={window.max():.6f}"
        )
        print(
            f"[INFERENCE] PROC window: shape={processed.shape}, mean={processed.mean():.6f}, "
            f"std={processed.std():.6f}, min={processed.min():.6f}, max={processed.max():.6f}"
        )
        print(f"[INFERENCE] First 3 raw samples: {window[:3, :min(3, window.shape[1])]}")
        print(f"[INFERENCE] First 3 proc samples: {processed[:3, :min(3, processed.shape[1])]}")

        try:
            prediction = model_service.predict(processed)
        except Exception as exc:
            import traceback

            print(f"[INFERENCE] Error during model.predict: {exc}")
            traceback.print_exc()
            return None

        try:
            print(
                f"[INFERENCE] Prediction: presence={prediction.get('presence')} "
                f"confidence={prediction.get('confidence'):.4f}"
            )
            print(f"[INFERENCE] Probabilities: {prediction.get('probability')}")

            prediction = self._publish_prediction(prediction)

            print(
                "[PREDICTION] "
                f"presence={prediction.get('presence')} "
                f"raw_presence={prediction.get('raw_presence')} "
                f"confidence={(float(prediction.get('confidence', 0.0)) * 100):.1f}% "
                f"timestamp={prediction['timestamp']}"
            )

            return prediction
        except Exception as exc:
            import traceback

            print(f"[INFERENCE] Unexpected error after prediction: {exc}")
            traceback.print_exc()
            return None


inference_service = InferenceService(
    window_size=int(os.getenv("WINDOW_SIZE", str(model_service.window_size))),
    step_size=int(os.getenv("STEP_SIZE", str(model_service.step_size))),
    feature_dim=int(os.getenv("FEATURE_DIM", str(model_service.feature_dim))),
)
