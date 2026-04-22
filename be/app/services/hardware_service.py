import os
import socket
import threading
import time

from app.core.app_state import app_state
from app.services.inference_service import inference_service

class HardwareService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.sock = None
        self.udp_port = int(os.getenv("UDP_PORT", "3333"))
        self.max_packet_size = int(os.getenv("UDP_PACKET_SIZE", "4096"))
        self.feature_dim = int(os.getenv("FEATURE_DIM", str(inference_service.feature_dim)))
        self.received_packets = 0
        self.accepted_packets = 0
        self.rejected_packets = 0
        self._last_stats_log_at = 0.0

    def start(self):
        if self.running:
            return

        self.running = True
        app_state.monitoring = True
        self.received_packets = 0
        self.accepted_packets = 0
        self.rejected_packets = 0
        self._last_stats_log_at = 0.0
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        print(
            f"[UDP] Listening on 0.0.0.0:{self.udp_port}, expected_feature_dim={self.feature_dim}"
        )

    def stop(self):
        self.running = False
        app_state.monitoring = False
        app_state.esp32_1_connected = False
        app_state.esp32_2_connected = False
        app_state.latest_prediction = None
        app_state.last_seen_esp32_1 = None
        app_state.last_seen_esp32_2 = None

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

            self.received_packets += 1

            line = data.decode(errors="ignore").strip()
            if not line:
                self.rejected_packets += 1
                continue

            device_id, csi_values = self._parse_packet(line)
            if csi_values is None:
                self.rejected_packets += 1
                if self.rejected_packets <= 5:
                    print(f"[UDP] Rejected packet: parse error. raw='{line[:120]}'")
                continue

            if len(csi_values) != self.feature_dim:
                self.rejected_packets += 1
                if self.rejected_packets <= 5:
                    print(
                        f"[UDP] Rejected packet: feature_dim mismatch (got={len(csi_values)}, expected={self.feature_dim})"
                    )
                continue

            self.accepted_packets += 1
            app_state.mark_esp32_seen(device_id)
            app_state.refresh_connections()

            now = time.time()
            if self.accepted_packets == 1:
                print(f"[UDP] First valid CSI packet received from esp32_{device_id}")
            if now - self._last_stats_log_at >= 2.0:
                self._last_stats_log_at = now
                print(
                    "[UDP] Stats "
                    f"received={self.received_packets} "
                    f"accepted={self.accepted_packets} "
                    f"rejected={self.rejected_packets}"
                )

            prediction = inference_service.handle_new_sample(csi_values)
            if prediction:
                print(
                    "Realtime action:",
                    prediction["action"],
                    "confidence:",
                    round(prediction["confidence"], 3),
                )

    @staticmethod
    def _parse_packet(line: str):
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if not parts:
            return 1, None

        first = parts[0].lower()
        if first in {"esp32_1", "esp32-1", "1"}:
            values = parts[1:]
            device_id = 1
        elif first in {"esp32_2", "esp32-2", "2"}:
            values = parts[1:]
            device_id = 2
        else:
            values = parts
            device_id = 1

        try:
            return device_id, [float(x) for x in values]
        except ValueError:
            return device_id, None

hardware_service = HardwareService()
