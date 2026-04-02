from datetime import datetime
import random

LABELS = ["walking", "standing", "sitting", "falling"]

class ModelService:
    def __init__(self):
        self.model = None
        self.loaded = False

    def load_model(self):
        # TODO: thay bằng load model thật
        self.loaded = True

    def predict(self, processed_segment):
        action = random.choice(LABELS)
        confidence = round(random.uniform(0.80, 0.98), 2)

        probabilities = {
            "walking": 0.05,
            "standing": 0.05,
            "sitting": 0.05,
            "falling": 0.05
        }
        probabilities[action] = confidence

        return {
            "action": action,
            "confidence": confidence,
            "probabilities": probabilities,
            "timestamp": datetime.now().isoformat()
        }

model_service = ModelService()