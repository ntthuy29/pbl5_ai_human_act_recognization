import os
import socket
import threading

from app.core.app_state import app_state
from app.services.inference_service import inference_service

class HardwareService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.sock = None
        self.udp_port = int(os.getenv("UDP_PORT", "3333"))
        self.max_packet_size = int(os.getenv("UDP_PACKET_SIZE", "4096"))
        self.feature_dim = int(os.getenv("FEATURE_DIM", "30"))

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
        app_state.esp32_1_connected = False
        app_state.esp32_2_connected = False

        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _read_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        sock.bind(("", self.udp_port))
        self.sock = sock

        while self.running:
            try:
                data, _addr = sock.recvfrom(self.max_packet_size)
            except socket.timeout:
                continue
            except OSError:
                break

            line = data.decode(errors="ignore").strip()
            if not line:
                continue

            try:
                csi_values = [float(x) for x in line.split(",")]
            except ValueError:
                continue

            if len(csi_values) != self.feature_dim:
                continue

            app_state.esp32_1_connected = True
            app_state.esp32_2_connected = True

            prediction = inference_service.handle_new_sample(csi_values)
            if prediction:
                print(
                    "Realtime action:",
                    prediction["action"],
                    "confidence:",
                    round(prediction["confidence"], 3),
                )

hardware_service = HardwareService()
