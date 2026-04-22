import time


class AppState:
    def __init__(self):
        self.model_loaded = False
        self.monitoring = False
        self.esp32_1_connected = False
        self.esp32_2_connected = False
        self.latest_prediction = None
        self.last_seen_esp32_1 = None
        self.last_seen_esp32_2 = None
        self.connection_timeout_seconds = 5.0

    def mark_esp32_seen(self, device_id: int):
        now = time.time()
        if device_id == 2:
            self.last_seen_esp32_2 = now
        else:
            self.last_seen_esp32_1 = now

    def refresh_connections(self):
        now = time.time()
        timeout = float(self.connection_timeout_seconds)

        self.esp32_1_connected = bool(
            self.last_seen_esp32_1 is not None and (now - self.last_seen_esp32_1) <= timeout
        )
        self.esp32_2_connected = bool(
            self.last_seen_esp32_2 is not None and (now - self.last_seen_esp32_2) <= timeout
        )

app_state = AppState()