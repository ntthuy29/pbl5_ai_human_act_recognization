class AppState:
    def __init__(self):
        self.model_loaded = False
        self.monitoring = False
        self.esp32_1_connected = False
        self.esp32_2_connected = False
        self.latest_prediction = None

app_state = AppState()