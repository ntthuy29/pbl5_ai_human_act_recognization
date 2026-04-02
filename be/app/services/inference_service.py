from app.core.app_state import app_state
from app.services.buffer_service import buffer_service
from app.services.preprocess_service import preprocess_service
from app.services.model_service import model_service
from app.services.history_service import history_service

class InferenceService:
    def handle_new_sample(self, sample):
        buffer_service.add_sample(sample)

        if not buffer_service.is_ready():
            return None

        window = buffer_service.get_window()
        processed = preprocess_service.process(window)
        prediction = model_service.predict(processed)

        app_state.latest_prediction = prediction
        history_service.add(prediction)

        return prediction

inference_service = InferenceService()