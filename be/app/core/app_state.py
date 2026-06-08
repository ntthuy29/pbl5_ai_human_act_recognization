from collections import deque


class AppState:
    def __init__(self):
        self.model_loaded = False
        self.monitoring = False
        self.event_loop = None
        self.active_session_id = None
        self.active_session_user_id = None
        # ESP32 duoc cam thu cong, khong kiem tra ket noi bang phan mem.
        self.esp32_1_connected = True
        self.esp32_2_connected = True
        self.latest_prediction = None

        # recent raw CSI samples received (list of numeric lists). Kept small.
        self.recent_raw_samples = deque(maxlen=200)

    def mark_esp32_seen(self, device_id: int):
        return

    def set_active_session(self, session_id: int, user_id: int):
        self.active_session_id = session_id
        self.active_session_user_id = user_id

    def clear_active_session(self):
        self.active_session_id = None
        self.active_session_user_id = None

    def refresh_connections(self):
        self.esp32_1_connected = True
        self.esp32_2_connected = True

    def push_raw_sample(self, sample):
        try:
            self.recent_raw_samples.append(sample)
        except Exception:
            pass


app_state = AppState()