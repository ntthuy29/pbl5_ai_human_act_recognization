from app.core.app_state import app_state

class HistoryService:
    def add(self, prediction):
        app_state.history.appendleft(prediction)

    def get_all(self):
        return list(app_state.history)

history_service = HistoryService()