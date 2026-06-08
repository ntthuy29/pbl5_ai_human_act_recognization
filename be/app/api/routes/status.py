from fastapi import APIRouter
import time

from app.core.app_state import app_state
from app.services.model_service import model_service
from app.services.hardware_service import hardware_service
from app.services.inference_service import inference_service

router = APIRouter()

@router.get("/status")
def get_status():
    if app_state.monitoring and not (hardware_service.thread and hardware_service.thread.is_alive()):
        if app_state.active_session_user_id is not None:
            hardware_service.start(user_id=app_state.active_session_user_id)
    app_state.refresh_connections()
    now = time.time()

    def seconds_since(ts):
        if ts is None:
            return None
        return round(now - ts, 3)

    buffer_fill_percent = round(
        min(1.0, len(inference_service.buffer) / max(1, inference_service.window_size)) * 100,
        1,
    )
    if len(inference_service.buffer) < inference_service.window_size:
        prediction_progress_percent = buffer_fill_percent
    else:
        prediction_progress_percent = round(
            min(1.0, inference_service._samples_since_last_prediction / max(1, inference_service.step_size)) * 100,
            1,
        )

    return {
        "success": True,
        "data": {
            "backend": "running",
            "model_loaded": app_state.model_loaded,
            "model_type": model_service.model_type,
            "window_size": model_service.window_size,
            "step_size": model_service.step_size,
            "input_shape": model_service.input_shape,
            "feature_dim": model_service.feature_dim,
            "esp32_1_connected": app_state.esp32_1_connected,
            "esp32_2_connected": app_state.esp32_2_connected,
            "monitoring": app_state.monitoring,
            "monitoring_session": {
                "session_id": app_state.active_session_id,
                "user_id": app_state.active_session_user_id,
                "active": bool(app_state.monitoring and app_state.active_session_id is not None),
            },
            "latest_prediction": app_state.latest_prediction,
            "live_prediction": {
                "buffer_size": len(inference_service.buffer),
                "window_size": inference_service.window_size,
                "step_size": inference_service.step_size,
                "samples_since_last_prediction": inference_service._samples_since_last_prediction,
                "samples_needed_for_first_prediction": max(
                    0,
                    inference_service.window_size - len(inference_service.buffer),
                ),
                "samples_needed_for_next_prediction": max(
                    0,
                    inference_service.step_size - inference_service._samples_since_last_prediction,
                ),
                "ready_for_prediction": (
                    len(inference_service.buffer) >= inference_service.window_size
                    and inference_service._samples_since_last_prediction >= inference_service.step_size
                ),
                "buffer_fill_percent": buffer_fill_percent,
                "prediction_progress_percent": prediction_progress_percent,
                "progress_percent": prediction_progress_percent,
            },
            "udp": {
                "received_packets": hardware_service.received_packets,
                "accepted_packets": hardware_service.accepted_packets,
                "rejected_packets": hardware_service.rejected_packets,
                "last_packet_seconds_ago": seconds_since(hardware_service.last_packet_at),
                "last_valid_packet_seconds_ago": seconds_since(hardware_service.last_valid_packet_at),
                "last_sender_ip": hardware_service.last_sender_ip,
                "last_sender_port": hardware_service.last_sender_port,
                "listener_thread_alive": bool(hardware_service.thread and hardware_service.thread.is_alive()),
                "socket_bound": hardware_service.sock is not None,
            },
        }
    }