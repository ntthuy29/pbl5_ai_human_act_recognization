import numpy as np

class PreprocessService:
    def process(self, window):
        arr = np.array(window, dtype=float)

        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)

        mean = arr.mean(axis=0, keepdims=True)
        std = arr.std(axis=0, keepdims=True) + 1e-8
        normalized = (arr - mean) / std

        return normalized

preprocess_service = PreprocessService()