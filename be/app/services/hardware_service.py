import threading
import time

# from nbconvert import export
# import serial

from app.core.app_state import app_state
from app.services.inference_service import inference_service

class HardwareService:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return

        self.running = True
        app_state.monitoring = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        app_state.monitoring = False

    def _read_loop(self):
        while self.running:
            # TODO: thay bằng dữ liệu thật từ ESP32
            fake_sample = [1.0, 2.0, 3.0, 4.0]
            app_state.esp32_1_connected = True
            app_state.esp32_2_connected = True

            inference_service.handle_new_sample(fake_sample)
            time.sleep(0.1)

hardware_service = HardwareService()
