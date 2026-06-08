# Hướng dẫn di chuyển: Từ Nhận diện Hành động sang Phát hiện Sự hiện diện

## Tổng quan
Hệ thống đã được cập nhật từ nhận diện hành động (walking/sitting/standing) sang phát hiện sự hiện diện của con người trong phòng (person/no_person).

## Các thay đổi chính

### 1. Backend API Schema
**File: `be/app/schemas/predict_schema.py`**
- Thay đổi: `action` → `presence`
- `PredictData` model hiện chứa trường `presence` thay vì `action`

```python
# Cũ
class PredictData(BaseModel):
    action: str
    
# Mới
class PredictData(BaseModel):
    presence: str
```

### 2. Model Service
**File: `be/app/services/model_service.py`**
- Cập nhật phương thức `predict()` để trả về `presence` thay vì `action`
- Labels mặc định: `["person", "no_person"]`

### 3. Inference Service
**File: `be/app/services/inference_service.py`**
- Cập nhật logging để hiển thị `presence` thay vì `action`
- Ví dụ: `Prediction: presence=person, confidence=0.95`

### 4. Hardware Service
**File: `be/app/services/hardware_service.py`**
- Cập nhật thông báo realtime từ "Realtime action" → "Realtime presence"

### 5. Pipeline Service
**File: `be/app/services/pipeline_service.py`**
- Đổi tên class: `ActionRecognitionPipeline` → `HumanPresenceDetectionPipeline`
- Cập nhật docstring để phản ánh mục đích mới

### 6. Frontend Type Definitions
**File: `fe/mobile/services/type.ts`**
- Thay đổi: `action: string` → `presence: string`
- Cập nhật `PredictionData` type

### 7. Frontend API Service
**File: `fe/mobile/services/api.ts`**
- `RawPrediction` type: `action` → `presence`
- Hàm `normalizePrediction()` cập nhật để sử dụng `presence`

### 8. Frontend UI Components

#### Home Screen
**File: `fe/mobile/app/(tabs)/home.tsx`**
- "Trạng thái hiện tại" → "Sự hiện diện"
- Cập nhật `latest?.action` → `latest?.presence`
- Cập nhật AI suggestions để phù hợp với phát hiện sự hiện diện

#### History Screen
**File: `fe/mobile/app/(tabs)/history.tsx`**
- "Lịch sử dự đoán" → "Lịch sử phát hiện"
- Cập nhật `item.action` → `item.presence`
- Style: `actionText` → `presenceText`
- Message rỗng: "Chưa có dữ liệu lịch sử phát hiện"

### 9. Debug & Training Scripts

#### Debug Model
**File: `be/debug_model.py`**
- Default labels: `["person", "no_person"]`
- Cập nhật: "Predicted action" → "Detected presence"
- Cập nhật error message để phản ánh detection

#### Training Template
**File: `be/TRAINING_TEMPLATE.py`**
- `CLASS_NAMES = ["person", "no_person"]`

#### Training Params Guide
**File: `be/TRAINING_PARAMS_GUIDE.md`**
- Cập nhật ví dụ: `class_names=["person", "no_person"]`

#### Checkpoint Utils
**File: `be/utils/checkpoint_utils.py`**
- Cập nhật docstring với `num_classes: int = 2` cho person/no_person

## Database

### Lưu ý về Compatibility
- Trường `payload` trong bảng `prediction_history` vẫn lưu trữ `action` từ dữ liệu cũ
- **Migration không bắt buộc**: Dữ liệu cũ sẽ được giữ nguyên
- Dữ liệu mới sẽ sử dụng trường `presence`

**Tùy chọn optional**: Nếu muốn cấu trúc dữ liệu nhất quán, có thể chạy migration:
```sql
-- Rename column trong PostgreSQL
ALTER TABLE prediction_history 
RENAME COLUMN payload TO payload_old;

-- Hoặc update JSON content
UPDATE prediction_history 
SET payload = jsonb_set(payload, '{presence}', payload->'action')
WHERE payload ? 'action';
```

## Quy trình cập nhật Model

### Khi huấn luyện model mới:
1. Sử dụng `TRAINING_TEMPLATE.py` với `CLASS_NAMES = ["person", "no_person"]`
2. Chắc chắn rằng model checkpoint bao gồm:
   - `class_names`: `["person", "no_person"]`
   - `standardizer_mu`, `standardizer_sigma`, `global_max_abs`
3. Thay thế `be/models/lstmcnn.pt` bằng model mới

### Verification:
```bash
cd be
python debug_model.py
# Kiểm tra output:
# - "Detected presence: person" hoặc "Detected presence: no_person"
# - "✓ Checkpoint contains all standardizers"
```

## API Endpoints (không thay đổi)
Tất cả endpoints vẫn giữ nguyên URL, chỉ response schema thay đổi:
- `POST /api/predict` - trả về `presence` thay vì `action`
- `GET /api/latest` - trả về `presence` thay vì `action`
- `GET /api/history` - items chứa `presence` thay vì `action`

## Kiểm tra hoàn chỉnh

### Backend:
```bash
cd be
python debug_model.py  # Kiểm tra model loaded đúng
python -m pytest tests/ # Nếu có test
```

### Frontend:
```bash
cd fe/mobile
npm install
npm start  # Expo dev server
# Kiểm tra:
# - Home screen hiển thị "Sự hiện diện"
# - History screen hiển thị "Lịch sử phát hiện"
# - Latest prediction sử dụng presence
```

## Ghi chú quan trọng

1. **Backward Compatibility**: Nếu cơ sở dữ liệu chứa dữ liệu cũ với trường `action`, nó vẫn có thể truy cập được nhưng không được sử dụng trong UI mới.

2. **Model Training**: Hãy chắc chắn rằng model được huấn luyện với 2 classes: person/no_person

3. **Feature Dimension**: Đảm bảo feature dimension khớp giữa model và config:
   - Mặc định: 30 hoặc 96 (tùy thuộc vào dữ liệu CSI)

4. **Standardizers**: Luôn lưu trữ standardizers (mu, sigma, max_abs) trong model checkpoint
