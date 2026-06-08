# Tóm Tắt Sửa Đổi

File này tóm tắt những gì đã được sửa ở backend và frontend, cùng với lý do của các thay đổi.

## 1. Xử lý `API base URL` ở frontend

### Đã thay đổi gì
- Thêm [fe/mobile/app.config.js](fe/mobile/app.config.js) để Expo đọc `EXPO_PUBLIC_API_BASE_URL` từ biến môi trường.
- Thêm [fe/mobile/.env.example](fe/mobile/.env.example) làm mẫu cấu hình URL API cục bộ.
- Thêm file [fe/mobile/.env](fe/mobile/.env) trên máy để app tự dùng IP LAN hiện tại.
- Cập nhật [fe/mobile/services/api.ts](fe/mobile/services/api.ts) để chuẩn hoá URL API và tự động gắn `/api` khi cần.

### Vì sao
- Trước khi sửa, app có thể rơi về host tunnel của Expo và tạo URL sai như `exp.direct:8000`.
- FE cần một cách ổn định để trỏ tới backend mà không phải sửa source code mỗi lần.
- Chuẩn hoá URL giúp tránh lỗi 404 do gọi `/status` và `/latest` mà thiếu tiền tố `/api`.

## 2. Hành vi màn hình Home

### Đã thay đổi gì
- Cập nhật nội dung trong [fe/mobile/app/(tabs)/home.tsx](fe/mobile/app/(tabs)/home.tsx) để nút chính phản ánh đúng hành vi thật: bật/tắt monitoring.
- Thêm nút dự đoán thủ công gọi thẳng `api.predict(...)`.
- Thêm kết nối websocket live-prediction để dashboard nhận prediction mới ngay khi backend tạo ra.
- Điều chỉnh polling của dashboard để trạng thái vẫn được cập nhật đều, còn prediction live thì được đẩy ngay lập tức.

### Vì sao
- Text nút cũ gợi ý rằng có luồng dự đoán thủ công, nhưng thực tế backend đang auto-inference từ dữ liệu CSI.
- App cần tách bạch rõ giữa điều khiển monitoring và hiển thị prediction.
- Cập nhật qua websocket giúp giao diện mang cảm giác realtime thay vì chỉ chờ polling.

## 3. Kiểu dữ liệu frontend

### Đã thay đổi gì
- Mở rộng [fe/mobile/services/type.ts](fe/mobile/services/type.ts) để khớp với response status từ backend, thêm các field:
  - `model_type`
  - `window_size`
  - `step_size`
  - `input_shape`
  - `udp`

### Vì sao
- Hàm predict thủ công cần `window_size` và `feature_dim` từ payload status của backend.
- Giữ type TypeScript khớp backend giúp tránh lỗi compile và làm code UI an toàn hơn.

## 4. Đẩy prediction live từ backend

### Đã thay đổi gì
- Thêm kênh websocket prediction trong [be/app/websocket/prediction_ws.py](be/app/websocket/prediction_ws.py).
- Đăng ký route websocket đó trong [be/app/main.py](be/app/main.py).
- Lưu event loop của FastAPI trong [be/app/core/app_state.py](be/app/core/app_state.py).
- Kích hoạt broadcast websocket từ cả hai luồng:
  - [be/app/services/inference_service.py](be/app/services/inference_service.py)
  - [be/app/services/prediction_service.py](be/app/services/prediction_service.py)

### Vì sao
- Backend đã tạo prediction từ stream CSI, nhưng frontend trước đây chỉ có polling.
- Broadcast prediction mới giúp FE cập nhật ngay khi backend sinh kết quả mới.
- Cách này giữ nguyên luồng CSI qua serial nhưng làm UI thật sự live.

## 5. Làm rõ kiến trúc

- ESP32 vẫn gửi CSI về backend qua serial.
- Backend vẫn là nơi chạy inference.
- Websocket chỉ dùng giữa backend và frontend.
- Nghĩa là không cần sửa websocket phía ESP32.

## 6. Lệnh chạy sau khi sửa

```powershell
cd d:\app_pbl5\be
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd d:\app_pbl5\fe\mobile
npx expo start --lan --clear
```

## 7. Ghi chú

- `--tunnel` có thể lỗi vì vấn đề tunnel của Expo/Ngrok; `--lan` thường ổn định hơn khi cùng Wi-Fi.
- Nếu IP máy tính thay đổi, hãy cập nhật `EXPO_PUBLIC_API_BASE_URL` trong [fe/mobile/.env](fe/mobile/.env).
