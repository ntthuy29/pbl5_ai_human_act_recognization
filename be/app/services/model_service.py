import os
from pathlib import Path
import numpy as np
import torch
from app.core.app_state import app_state
from models.model import build_model

class ModelService:
    def __init__(self, model_path: str, feature_dim: int):
        self.model_path = model_path
        checkpoint = torch.load(model_path, map_location="cpu", 
                                weights_only=False)

        self.model_type = self._infer_model_type(checkpoint)
        self.input_shape = self._infer_input_shape(checkpoint, feature_dim)
        self.window_size = self._infer_window_size(checkpoint, self.input_shape, self.model_type)
        self.step_size = self._infer_step_size(checkpoint, self.window_size)
        self.spectrogram_nperseg = self._infer_spectrogram_nperseg(checkpoint)
        self.feature_dim = self._infer_feature_dim(checkpoint, feature_dim)
        num_classes = self._infer_num_classes(checkpoint, default=2)
        self.labels = self._infer_labels(checkpoint, num_classes)

        # Load standardizers from checkpoint for real-time preprocessing
        self.standardizer_mu = checkpoint.get("standardizer_mu")
        self.standardizer_sigma = checkpoint.get("standardizer_sigma")
        self.global_max_abs = checkpoint.get("global_max_abs")
        
        has_standardizers = (
            self.standardizer_mu is not None and
            self.standardizer_sigma is not None and
            self.global_max_abs is not None
        )
        
        if has_standardizers:
            print(f"[MODEL] ✓ Loaded standardizers from checkpoint")
            print(f"  - standardizer_mu shape: {self.standardizer_mu.shape}")
            print(f"  - standardizer_sigma shape: {self.standardizer_sigma.shape}")
            print(f"  - global_max_abs: {self.global_max_abs}")
        else:
            print(f"[MODEL] ⚠️  WARNING: Standardizers NOT found in checkpoint!")
            print(f"  Model path: {model_path}")
            print(f"  Checkpoint keys: {list(checkpoint.keys())}")

        self.model = self._build_model_from_checkpoint(checkpoint, num_classes)
        self.model.eval()
        app_state.model_loaded = True

    def predict(self, processed_window: np.ndarray) -> dict:
        x = torch.tensor(processed_window, dtype=torch.float32)
        if self.model_type == "cnn2d":
            if x.ndim == 3:
                x = x.permute(2, 0, 1).unsqueeze(0)
            elif x.ndim == 4 and x.shape[-1] == self.feature_dim:
                x = x.permute(0, 3, 1, 2)
            elif x.ndim == 2:
                x = x.unsqueeze(0).unsqueeze(0)
        else:
            if x.ndim == 2:
                x = x.unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1).numpy()[0]
        idx = int(np.argmax(probs))
        presence = self.labels[idx]
        raw_probabilities = dict(zip(self.labels, probs.tolist()))
        return {
            "presence": presence,
            "confidence": float(probs[idx]),
            "probability": raw_probabilities,
            "raw_probabilities": raw_probabilities,
            "probabilities": raw_probabilities,
        }

    @staticmethod
    def _extract_state_dict(checkpoint):
        if isinstance(checkpoint, dict):
            state_dict = checkpoint.get("state_dict")
            if isinstance(state_dict, dict):
                return state_dict

            model_state_dict = checkpoint.get("model_state_dict")
            if isinstance(model_state_dict, dict):
                return model_state_dict

            model_obj = checkpoint.get("model")
            if hasattr(model_obj, "state_dict"):
                return model_obj.state_dict()

        if isinstance(checkpoint, dict):
            return checkpoint

        if hasattr(checkpoint, "state_dict"):
            return checkpoint.state_dict()

        raise TypeError("Unsupported checkpoint format: cannot extract state_dict")

    def _build_model_from_checkpoint(self, checkpoint, num_classes: int):
        state_dict = self._extract_state_dict(checkpoint)
        candidates = []
        for candidate in [self.model_type, os.getenv("MODEL_TYPE")]:
            if candidate:
                normalized = str(candidate).strip().lower()
                if normalized and normalized not in candidates:
                    candidates.append(normalized)
        for fallback in ["lstmcnn", "cnn2d"]:
            if fallback not in candidates:
                candidates.append(fallback)

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                model = build_model(candidate, input_shape=self.input_shape, num_classes=num_classes)
                model.load_state_dict(state_dict)
                self.model_type = candidate
                print(f"[MODEL] ✓ Loaded model_type={candidate}")
                return model
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            f"Unable to build model from checkpoint. Tried {candidates}. Last error: {last_error}"
        )
    @staticmethod
    def _get_from_checkpoint_config(checkpoint, keys):
        if not isinstance(checkpoint, dict):
            return None
        sources = [
            checkpoint, 
            checkpoint.get("args"),
            checkpoint.get("training_config"),


        ]
        for source in sources: 
            if isinstance(source, dict):
                for key in keys:
                    value = source.get(key)
                    if value is not None:
                        try: 
                            return int(value)
                        except (TypeError, ValueError):
                            pass
        return None

    @staticmethod
    def _infer_model_type(checkpoint) -> str:
        if isinstance(checkpoint, dict):
            for source in (
                checkpoint, 
                checkpoint.get("args"),
                checkpoint.get("training_config"),
            ): 
                if isinstance(source, dict):
                    model_type = source.get("model_type")
                    if model_type: 
                        return str(model_type).lower()
        return os.getenv("MODEL_TYPE", "lstmcnn").lower()

    @staticmethod
    def _infer_input_shape(checkpoint, fallback_feature_dim: int):
        if isinstance(checkpoint, dict):
            input_shape = checkpoint.get("input_shape")
            if isinstance(input_shape, (tuple, list)) and len(input_shape) > 0:
                return tuple(int(v) for v in input_shape)
        return (int(os.getenv("WINDOW_SIZE", "128")), int(fallback_feature_dim))

    @staticmethod
    def _infer_window_size(checkpoint, input_shape, model_type: str) -> int:
        value = ModelService._get_from_checkpoint_config(
            checkpoint,
            ("window_size", "sequence_length", "time_steps"),
        )
        if value is not None: 
            return value
        if model_type.lower() == "lstmcnn": 
            if isinstance(input_shape, (tuple, list)) and len(input_shape) > 0:
                try: 
                    return int(input_shape[0])
                except (TypeError, ValueError):
                    pass
        return int(os.getenv("WINDOW_SIZE", "128"))
    @staticmethod
    def _infer_step_size(checkpoint, window_size: int) -> int:
        value = ModelService._get_from_checkpoint_config(
            checkpoint,
            ("step_size", "step", "stride"),
        )
        if value is not None: 
            return value
        return max(1, window_size // 2)
    @staticmethod
    def _infer_spectrogram_nperseg(checkpoint) -> int:
        value = ModelService._get_from_checkpoint_config(
            checkpoint,
            ("spectrogram_nperseg", "nperseg"),
        )
        if value is not None: 
            return value
        return int(os.getenv("SPECTROGRAM_NPERSEG", "64"))

    @staticmethod
    def _infer_feature_dim(checkpoint, fallback_feature_dim: int) -> int:
        if isinstance(checkpoint, dict):
            input_shape = checkpoint.get("input_shape")
            if isinstance(input_shape, (tuple, list)) and len(input_shape) > 0:
                try:
                    return int(input_shape[-1])
                except (TypeError, ValueError):
                    pass
        return int(fallback_feature_dim)

    @staticmethod
    def _infer_num_classes(checkpoint, default: int = 3) -> int:
        if isinstance(checkpoint, dict):
            class_names = checkpoint.get("class_names")
            if isinstance(class_names, (tuple, list)) and len(class_names) > 0:
                return len(class_names)

            num_classes = checkpoint.get("num_classes")
            if num_classes is not None:
                try:
                    return int(num_classes)
                except (TypeError, ValueError):
                    pass

        return default

    @staticmethod
    def _infer_labels(checkpoint, num_classes: int):
        if isinstance(checkpoint, dict):
            class_names = checkpoint.get("class_names")
            if isinstance(class_names, (tuple, list)) and len(class_names) == num_classes:
                return [str(name) for name in class_names]

        default_labels = ["person", "no_person"]
        if num_classes == len(default_labels):
            return default_labels
        return [f"class_{i}" for i in range(num_classes)]

    @staticmethod
    def _default_model_path() -> str:
        configured = os.getenv("MODEL_PATH")
        if configured and Path(configured).is_file():
            return configured
        base_dir = Path(__file__).resolve().parents[2]
        return str(base_dir / "models" / "lstmcnn.pt")
    
    @staticmethod
    def _default_feature_dim() -> int:
        return int(os.getenv("FEATURE_DIM", "30"))

model_service = ModelService(
    model_path = ModelService._default_model_path(),
    feature_dim = ModelService._default_feature_dim()
)