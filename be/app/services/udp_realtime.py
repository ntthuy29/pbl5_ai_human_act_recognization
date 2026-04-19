# udp_realtime_lan.py
import socket
import numpy as np
from collections import deque
from app.services.inference_service import inference_service

# ================= Cấu hình =================
UDP_PORT = 3333            # port ESP32 RX gửi CSI
FEATURE_DIM = 30           # số subcarriers đúng với model
WINDOW_SIZE = 128          # window size pipeline
STEP_SIZE = 64             # step size trượt window
SMOOTH_WINDOW = 3          # số dự đoán gần nhất để majority vote

# ================= Buffer + Smoothing =================
csi_buffer = deque(maxlen=WINDOW_SIZE)
action_history = deque(maxlen=SMOOTH_WINDOW)

# ================= UDP Socket =================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))  # lắng nghe tất cả IP của máy app
print(f"Listening for CSI from ESP32 RX on UDP port {UDP_PORT}...")

# ================= Majority Vote =================
def majority_vote(history):
    if not history:
        return None
    counts = {}
    for act in history:
        counts[act] = counts.get(act, 0) + 1
    return max(counts, key=counts.get)

# ================= Main Loop =================
while True:
    data, addr = sock.recvfrom(2048)
    line = data.decode(errors="ignore").strip()
    if not line:
        continue

    # parse CSV CSI: "amp0,amp1,..."
    try:
        csi_values = [float(x) for x in line.split(",")]
    except ValueError:
        continue

    # kiểm tra đúng số feature
    if len(csi_values) != FEATURE_DIM:
        continue

    # ---- Thêm vào buffer ----
    csi_buffer.append(csi_values)

    # ---- Khi đủ window ----
    if len(csi_buffer) >= WINDOW_SIZE and len(csi_buffer) % STEP_SIZE == 0:
        window = np.array(csi_buffer)
        prediction = inference_service.handle_new_sample(window)
        if prediction:
            # majority vote smoothing
            action_history.append(prediction["action"])
            stable_action = majority_vote(action_history)
            print(f"Realtime action: {stable_action}, confidence: {prediction['confidence']:.2f}")