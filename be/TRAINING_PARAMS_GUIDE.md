## 📋 Hướng dẫn: Lưu Training Parameters vào Checkpoint

Để backend dự đoán chính xác, cần đảm bảo **preprocessing realtime trùng với training**.
Điều này yêu cầu lưu `standardizer_mu`, `standardizer_sigma`, `global_max_abs` vào checkpoint.

---

## 🎯 3 Cách Làm (Chọn 1 trong 3)

### **Cách 1: Sử dụng Training Script mới (Khuyến nghị)**

Nếu bạn đang training model từ đầu:

#### Step 1: Chuẩn bị training script
```python
# Sử dụng template: TRAINING_TEMPLATE.py
# Thay thế:
#   - train_loader: load dữ liệu training
#   - FEATURE_DIM, NUM_CLASSES, CLASS_NAMES
```

#### Step 2: Training script sẽ tự động compute standardizers
```python
from utils.checkpoint_utils import compute_standardizers_from_dataset

mu, sigma, max_abs = compute_standardizers_from_dataset(train_loader)
```

#### Step 3: Save checkpoint với standardizers
```python
from utils.checkpoint_utils import save_checkpoint

save_checkpoint(
    model=model,
    optimizer=optimizer,
    epoch=NUM_EPOCHS,
    save_path="models/lstmcnn.pt",
    input_shape=(128, 30),
    num_classes=3,
    class_names=["person", "no_person"],
    standardizer_mu=mu,
    standardizer_sigma=sigma,
    global_max_abs=max_abs,
)
```

#### Step 4: Verify
```bash
python be/check_model.py
```
Kết quả sẽ hiện `✓` cho standardizer_mu/sigma/max_abs.

---

### **Cách 2: Update Checkpoint cũ (Nếu có training data)**

Nếu bạn đã có checkpoint nhưng thiếu standardizers:

#### Step 1: Chuẩn bị training data
- Save training data thành numpy file: `train_data.npy`
- Shape: `(n_samples * n_time, feature_dim)` hoặc `(n_samples, n_time, feature_dim)`
- Example: `(10000, 30)` hoặc `(100, 128, 30)`

#### Step 2: Update checkpoint
```bash
cd d:\app_pbl5\be
python update_checkpoint.py \
  --checkpoint models/lstmcnn.pt \
  --data train_data.npy \
  --output models/lstmcnn_updated.pt
```

Hoặc ghi đè checkpoint cũ:
```bash
python update_checkpoint.py \
  --checkpoint models/lstmcnn.pt \
  --data train_data.npy
```

#### Step 3: Verify
```bash
python be/check_model.py
```

---

### **Cách 3: Tính từ realtime data (Khẩn cấp)**

Nếu không có training data sẵn, có thể tính từ dữ liệu sensor realtime:

```python
import numpy as np
from utils.checkpoint_utils import update_checkpoint_with_standardizers

# Collect realtime data từ hardware_service
# Tạm dừng inference, chỉ collect data từ serial
# Lấy ~1000-5000 samples

collected_data = np.array([...]).astype(np.float32)  # shape: (n_samples, 30)

mu = collected_data.mean(axis=0)
sigma = collected_data.std(axis=0)
max_abs = np.max(np.abs(collected_data))

update_checkpoint_with_standardizers(
    checkpoint_path="models/lstmcnn.pt",
    standardizer_mu=mu,
    standardizer_sigma=sigma,
    global_max_abs=max_abs,
)
```

---

## 🔍 Verify: Check Model Có Standardizers

```bash
cd d:\app_pbl5\be
python check_model.py
```

**Output tốt:**
```
=== STANDARDIZERS ===
standardizer_mu: ✓
  mu shape: (30,)
standardizer_sigma: ✓
  sigma shape: (30,)
global_max_abs: ✓
  max_abs: 15.234
```

**Output xấu (cần fix):**
```
=== STANDARDIZERS ===
standardizer_mu: ✗
standardizer_sigma: ✗
global_max_abs: ✗

⚠️  WARNING: Standardizers missing from checkpoint
    → This WILL cause prediction mismatch.
```

---

## 📊 Điều gì xảy ra sau khi update checkpoint?

### **Backend load checkpoint:**
```python
# ModelService.__init__
self.standardizer_mu = checkpoint.get("standardizer_mu")
self.standardizer_sigma = checkpoint.get("standardizer_sigma")
self.global_max_abs = checkpoint.get("global_max_abs")
```

### **Preprocessing realtime sẽ dùng full pipeline:**
```
RAW Data (từ ESP32 serial)
  ↓
Hampel filter (outlier removal)
  ↓
Butterworth low-pass (noise smoothing)
  ↓
Standardizer: (x - mu) / sigma  ← Dùng training params
  ↓
Global normalization: x / max_abs  ← Dùng training params
  ↓
Model.predict()
```

Nếu thiếu standardizers, chỉ dùng 2 bước đầu → sai.

---

## ⚡ Quick Summary

| Tình huống | Giải pháp |
|---|---|
| **Training từ đầu** | Dùng `TRAINING_TEMPLATE.py` + `save_checkpoint()` |
| **Có checkpoint cũ + training data** | Dùng `update_checkpoint.py --data train_data.npy` |
| **Khẩn cấp, không có data** | Collect realtime data + tính standardizers |
| **Verify checkpoint** | Chạy `python check_model.py` |

---

## 🚀 Usage Examples

### Example 1: Training script đầy đủ
```python
# be/train_my_model.py (dựa trên TRAINING_TEMPLATE.py)
from utils.checkpoint_utils import (
    save_checkpoint,
    compute_standardizers_from_dataset,
)

# ... training loop ...

mu, sigma, max_abs = compute_standardizers_from_dataset(train_loader)

save_checkpoint(
    model=model,
    optimizer=optimizer,
    epoch=epoch,
    save_path="models/lstmcnn.pt",
    input_shape=(WINDOW_SIZE, FEATURE_DIM),
    num_classes=NUM_CLASSES,
    class_names=CLASS_NAMES,
    standardizer_mu=mu,
    standardizer_sigma=sigma,
    global_max_abs=max_abs,
)
```

### Example 2: Update checkpoint từ data
```bash
# 1. Save training data
python -c "import numpy as np; data = np.random.randn(10000, 30).astype(np.float32); np.save('train_data.npy', data)"

# 2. Update checkpoint
cd be
python update_checkpoint.py --checkpoint models/lstmcnn.pt --data ../train_data.npy

# 3. Verify
python check_model.py
```

### Example 3: Compute standardizers từ code
```python
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "be"))

from utils.checkpoint_utils import update_checkpoint_with_standardizers

# Giả sử có training data
train_data = np.random.randn(10000, 30).astype(np.float32)
mu = train_data.mean(axis=0)
sigma = train_data.std(axis=0)
max_abs = np.max(np.abs(train_data))

update_checkpoint_with_standardizers(
    checkpoint_path="be/models/lstmcnn.pt",
    standardizer_mu=mu,
    standardizer_sigma=sigma,
    global_max_abs=max_abs,
)
```

---

## 🐛 Troubleshooting

**Q: Checkpoint đã có standardizers nhưng model vẫn sai?**
A: Kiểm tra:
  1. `check_model.py` có in "✓ Using FULL preprocessing" không?
  2. Standardizer params có khớp với training không?
  3. Feature_dim có khớp không?

**Q: Preprocessing params (Hampel window, Butterworth cutoff) khác training?**
A: Trong `be/app/services/inference_service.py`, mặc định:
  - hampel_window_size=5, hampel_n_sigmas=3.0
  - butter_order=4, butter_cutoff=0.1
  
Nếu training khác, cần update hoặc lưu thêm vào checkpoint.

**Q: Training data ở đâu?**
A: 
  - Nếu training offline: save vào numpy file
  - Nếu training từ raw CSV: load → reshape → save .npy
  - Nếu từ database: query → numpy array → save .npy

---

## 📚 Files liên quan

- `be/utils/checkpoint_utils.py` - Utility functions
- `be/TRAINING_TEMPLATE.py` - Training script template
- `be/update_checkpoint.py` - Script update checkpoint
- `be/check_model.py` - Verify checkpoint
- `be/debug_model.py` - Debug inference pipeline
- `be/app/services/model_service.py` - Load checkpoint
- `be/app/services/inference_service.py` - Realtime preprocessing
