from collections import deque

class AppState:
    def __init__(self):
        self.model_loaded = False
        self.monitoring = False
        self.esp32_1_connected = False
        self.esp32_2_connected = False
        self.latest_prediction = None
        self.history = deque(maxlen=100)

app_state = AppState()