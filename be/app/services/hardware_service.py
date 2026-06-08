import os
import threading
import time
from datetime import datetime, timezone

import serial
from serial import SerialException
from sqlalchemy import select

from app.core.app_state import app_state
from app.db.session import SessionLocal
from app.models.monitoring_session import MonitoringSession
from app.services.inference_service import inference_service
from app.services.model_service import model_service
# serial_conn: đối tượng kết nối tới port
class HardwareService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.serial_conn = None
        # Keep this attribute for compatibility with existing status route.
        self.sock = None
        self.serial_port = os.getenv("SERIAL_PORT", "COM3")
        self.serial_baudrate = int(os.getenv("SERIAL_BAUDRATE", "115200"))
        self.raw_feature_dim = int(os.getenv("RAW_CSI_FEATURE_DIM", "128"))
        # Use model feature_dim from checkpoint, fallback to env or inference_service
        self.feature_dim = int(os.getenv("FEATURE_DIM", str(model_service.feature_dim)))
        self.received_packets = 0
        self.accepted_packets = 0
        self.rejected_packets = 0
        self.last_packet_at = None
        self.last_valid_packet_at = None
        self.last_sender_ip = None
        self.last_sender_port = None
        self._last_stats_log_at = 0.0
        self._last_error_log_at = 0.0
        self._consecutive_connect_failures = 0
        self._base_retry_delay = float(os.getenv("SERIAL_RETRY_BASE_SECONDS", "1.0"))
        self._max_retry_delay = float(os.getenv("SERIAL_RETRY_MAX_SECONDS", "10.0"))
        self._error_log_cooldown = float(os.getenv("SERIAL_ERROR_LOG_COOLDOWN_SECONDS", "5.0"))
        self._last_heartbeat_at = 0.0
        self._idle_counter = 0
        self._active_session_db_id = None

    def _close_serial_safely(self):
        conn = self.serial_conn
        self.serial_conn = None # chỉ reset reference trong class, không ảnh hưởng đến việc đóng kết nối thực tế
        self.sock = None

        if not conn:
            return

        try:
            conn.close() # đóng kết nối thực tế, nếu đã mở thành công
        except (SerialException, AttributeError, OSError):
            pass

    def start(self, user_id: int | None = None):
        if self.running and self.thread and self.thread.is_alive():
            return

        if self.running and (not self.thread or not self.thread.is_alive()):
            print("THREAD đã chết nhưng trạng thái vẫn là running=True, đang reset lại trạng thái để khởi động lại thread")
            self.running = False # ép về trạng thái dừng

        self.running = True
        app_state.monitoring = True
        self.received_packets = 0
        self.accepted_packets = 0
        self.rejected_packets = 0
        self.last_packet_at = None
        self.last_valid_packet_at = None
        self.last_sender_ip = None
        self.last_sender_port = None
        self._last_stats_log_at = 0.0
        self._last_error_log_at = 0.0
        self._consecutive_connect_failures = 0
        inference_service.reset()
        app_state.latest_prediction = None
        if user_id is not None:
            app_state.active_session_user_id = user_id
        self._create_session_if_needed()
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        print(
            f"[SERIAL] Starting reader on {self.serial_port} @ {self.serial_baudrate}, "
            f"expected_feature_dim={self.feature_dim}"
        )

    def stop(self):
        self.running = False
        app_state.monitoring = False
        self.last_packet_at = None
        self.last_valid_packet_at = None
        self.last_sender_ip = None
        self.last_sender_port = None
        self._consecutive_connect_failures = 0
        self._close_serial_safely() # đóng port
        self._close_session_if_needed()

    def _create_session_if_needed(self):
        if self._active_session_db_id is not None:
            return

        user_id = app_state.active_session_user_id
        if user_id is None:
            raise RuntimeError("Cannot start monitoring session without authenticated user")

        with SessionLocal() as db:
            session = MonitoringSession(user_id=user_id, is_active=True)
            db.add(session)
            db.commit()
            db.refresh(session)

            self._active_session_db_id = session.id
            app_state.set_active_session(session.id, user_id)

    def _close_session_if_needed(self):
        session_id = self._active_session_db_id
        if session_id is None:
            app_state.clear_active_session()
            return

        with SessionLocal() as db:
            session = db.execute(
                select(MonitoringSession).where(MonitoringSession.id == session_id)
            ).scalar_one_or_none()

            if session is not None:
                session.is_active = False
                session.ended_at = datetime.now(timezone.utc)
                db.add(session)
                db.commit()

        self._active_session_db_id = None
        app_state.clear_active_session()

    def _read_loop(self):
        while self.running:
            try:
                if self.serial_conn is None:
                    self.serial_conn = serial.Serial(
                        port=self.serial_port,
                        baudrate=self.serial_baudrate,
                        timeout=1,
                        write_timeout=1,
                    )
                    # Keep this attribute aligned with existing status route.
                    self.sock = self.serial_conn
                    self._consecutive_connect_failures = 0
                    print(
                        f"[SERIAL] Connected to {self.serial_port} @ {self.serial_baudrate}"
                    )

                raw = self.serial_conn.readline() # đọc một dòng dữ liệu từ cổng serial
            except SerialException as exc:
                self._consecutive_connect_failures += 1
                retry_delay = min(
                    self._max_retry_delay,
                    self._base_retry_delay * (2 ** max(0, self._consecutive_connect_failures - 1)),
                )

                now = time.time()
                should_log = now - self._last_error_log_at >= self._error_log_cooldown
                if should_log:
                    self._last_error_log_at = now
                    message = f"[SERIAL] Connection error on {self.serial_port}: {exc}"
                    if "Access is denied" in str(exc):
                        message += " | COM port is busy. Close Serial Monitor/other apps that use this port."
                    message += (
                        f" | retry_in={retry_delay:.1f}s"
                        f" failure_count={self._consecutive_connect_failures}"
                    )
                    print(message)

                self._close_serial_safely()
                time.sleep(retry_delay)
                continue
            except Exception as exc:
                print(f"[SERIAL] Unexpected read error: {exc}")
                self._close_serial_safely()
                time.sleep(1.0)
                continue

            if not raw:
                # No data read this iteration - increment idle counter and occasionally print heartbeat
                self._idle_counter += 1
                now = time.time()
                if now - self._last_heartbeat_at >= 5.0:
                    self._last_heartbeat_at = now
                    last_packet_seconds_ago = None
                    last_valid_packet_seconds_ago = None
                    try:
                        if self.last_packet_at:
                            last_packet_seconds_ago = now - self.last_packet_at
                        if self.last_valid_packet_at:
                            last_valid_packet_seconds_ago = now - self.last_valid_packet_at
                    except Exception:
                        pass

                    conn_state = 'connected' if self.serial_conn else 'not_connected'
                    print(
                        f"[SERIAL HEARTBEAT] state={conn_state} received={self.received_packets} "
                        f"accepted={self.accepted_packets} rejected={self.rejected_packets} "
                        f"last_packet_seconds_ago={last_packet_seconds_ago} "
                        f"last_valid_packet_seconds_ago={last_valid_packet_seconds_ago}"
                    )

                continue

            line = raw.decode(errors="ignore").strip()
            if not line:
                continue

            self.received_packets += 1
            self.last_packet_at = time.time()
            self.last_sender_ip = "serial"
            self.last_sender_port = self.serial_port

            # print(f"[SERIAL RAW] {line[:200]}")

            rssi, csi_values = self._parse_packet(line)
            if csi_values is None:
                self.rejected_packets += 1
                # print(f"[SERIAL REJECTED] parse error raw='{line[:120]}'")
                continue

            if len(csi_values) != self.raw_feature_dim:
                self.rejected_packets += 1
                continue

            self.accepted_packets += 1
            self.last_valid_packet_at = time.time()
            app_state.refresh_connections()
            # store raw sample for inspection
            try:
                app_state.push_raw_sample([rssi, *csi_values])
            except Exception:
                pass

            # print raw CSI (truncated preview and full sample)
            try:
                sample_preview = csi_values if len(csi_values) <= 40 else csi_values[:40]
                print(f"[SERIAL ACCEPTED] rssi={rssi}, features={len(csi_values)}, sample_preview={sample_preview} (showing up to 40 values)")
                # Also print the full CSI line for immediate terminal inspection
                try:
                    print(f"[SERIAL RAW FULL] rssi={rssi}, csi_iq={csi_values}")
                except Exception:
                    pass
            except Exception:
                print(f"[SERIAL ACCEPTED] rssi={rssi}, features={len(csi_values)}")
            print(f"[SERIAL] total_received={self.received_packets} total_accepted={self.accepted_packets} rejected={self.rejected_packets}")

            now = time.time()
            if now - self._last_stats_log_at >= 5.0:
                self._last_stats_log_at = now
                print(
                    "[SERIAL STATS] "
                    f"received={self.received_packets} "
                    f"accepted={self.accepted_packets} "
                    f"rejected={self.rejected_packets} "
                    f"accept_rate={100*self.accepted_packets/max(1, self.received_packets):.1f}%"
                )

            # Debug: report current inference buffer state before sending sample
            try:
                buf_len = len(inference_service.buffer)
                win = inference_service.window_size
                step = inference_service.step_size
                samples_since = inference_service._samples_since_last_prediction
                progress = 100.0 * buf_len / max(1, win)
                print(f"[SERIAL->INFER] sending sample -> buffer={buf_len}/{win} progress={progress:.1f}% samples_since_last_prediction={samples_since}/{step}")
            except Exception:
                pass

            try:
                prediction = inference_service.handle_new_sample(csi_values)
            except Exception as exc:
                print(f"[INFERENCE] Error while handling sample: {exc}")
                continue

            # Debug: if no prediction produced, show buffer state
            if not prediction:
                try:
                    buf_len = len(inference_service.buffer)
                    win = inference_service.window_size
                    progress = 100.0 * buf_len / max(1, win)
                    print(f"[INFERENCE] No prediction yet. buffer={buf_len}/{win} progress={progress:.1f}%")
                except Exception:
                    pass
            if prediction:
                print(
                    f"[PREDICTION RESULT] presence={prediction['presence']} "
                    f"confidence={(float(prediction['confidence']) * 100):.1f}%"
                )

        self.running = False
        app_state.monitoring = False
        self._close_serial_safely()
        self._close_session_if_needed()

    def _parse_packet(self, line: str):
        parts = [p.strip() for p in line.split(",")]
        expected_len = self.raw_feature_dim + 1
        if len(parts) != expected_len:
            return None, None

        try:
            rssi = int(parts[0])
            csi_iq = [int(value) for value in parts[1:]]
        except ValueError:
            return None, None

        if len(csi_iq) != self.raw_feature_dim:
            return None, None

        return rssi, csi_iq

hardware_service = HardwareService()
