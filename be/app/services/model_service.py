import os
from pathlib import Path
import numpy as np
import torch
from app.core.app_state import app_state
from models.model import LstmCnnClassifier

class ModelService:
    def __init__(self, model_path: str, feature_dim: int):
        self.model_path = model_path
        checkpoint = torch.load(model_path, map_location="cpu")

        self.feature_dim = self._infer_feature_dim(checkpoint, feature_dim)
        num_classes = self._infer_num_classes(checkpoint, default=3)
        self.labels = self._infer_labels(checkpoint, num_classes)

        self.model = LstmCnnClassifier(feature_dim=self.feature_dim, num_classes=num_classes)
        self.model.load_state_dict(self._extract_state_dict(checkpoint))
        self.model.eval()
        app_state.model_loaded = True

    def predict(self, processed_window: np.ndarray) -> dict:
        x = torch.tensor(processed_window, dtype=torch.float32)
        if x.ndim == 2:
            x = x.unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1).numpy()[0]
        idx = int(np.argmax(probs))
        return {
            "action": self.labels[idx],
            "confidence": float(probs[idx]),
            "probability": dict(zip(self.labels, probs.tolist())),
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

        default_labels = ["walking", "sitting", "standing"]
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