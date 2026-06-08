# pipeline_service.py
import numpy as np
from collections import deque
from preprocess_service import PreprocessService
from model_service import ModelService

class HumanPresenceDetectionPipeline:
    def __init__(self, model_path: str, feature_dim: int, window_size: int = 128, step_size: int = 64):
        self.buffer = deque(maxlen=window_size)  # lưu CSI realtime
        self.window_size = window_size
        self.step_size = step_size
        self.preprocess = PreprocessService()
        self.model_service = ModelService(model_path=model_path, feature_dim=feature_dim)
        self._step_counter = 0

    def add_csi_sample(self, csi_sample: np.ndarray) -> dict | None:
        """
        Thêm 1 mẫu CSI realtime vào buffer.
        Trả về kết quả phát hiện khi đủ window, else None.
        """
        self.buffer.append(csi_sample)
        self._step_counter += 1

        if self._step_counter >= self.step_size and len(self.buffer) == self.window_size:
            # Lấy window từ buffer
            window = np.array(self.buffer)
            processed = self.preprocess.process(window)  # normalize, reshape
            result = self.model_service.predict(processed)

            # reset step counter để trượt window tiếp
            self._step_counter = 0
            return result

        return None