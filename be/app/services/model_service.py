import os
from pathlib import Path
import numpy as np
import torch
from models.model import LstmCnnClassifier

class ModelService: 
    def init(self, model_path:str, feature_dim: int):
        self.model_path = model_path
        self.feature_dim = feature_dim
        self.model = LstmCnnClassifier(feature_dim=feature_dim, num_class= 3) # hàm này sẽ khởi tạo mô hình LstmCnnClassifier với số lượng lớp đầu ra là 3 (tương ứng với 3 loại hành động)
        self.model.load_state_dict(torch.load(model_path, map_location="cpu")) # hàm này sẽ tải trọng số của mô hình đã được huấn luyện từ tệp tin được chỉ định bởi model_path và gán chúng cho mô hình hiện tại. Tham số map_location="cpu" đảm bảo rằng mô hình được tải lên CPU, ngay cả khi nó được huấn luyện trên GPU.
        self.model.eval() # hàm này sẽ đặt mô hình ở chế độ đánh giá, tắt dropout và batch normalization
        self.labels= ["walking", "sitting", "standing"] # danh sách các nhãn tương ứng với các lớp đầu ra của mô hình
        
        def predict (self, processed_window: np.ndarray)->dict:
            x = torch.tensor(processed_window, dtype = torch.float32) # hàm này sẽ chuyển đổi cửa sổ đã được xử lý thành một tensor PyTorch có kiểu dữ liệu float32
            if x.ndim == 2: # nếu tensor có 2 chiều tức là có dạng (sequence_length, feature_dim), thì chúng ta sẽ thêm một chiều batch vào đầu tensor để có dạng (1, sequence_length, feature_dim)
                x = x.unsqueeze(0)
            with torch.no_grad(): # hàm này sẽ tắt tính toán gradient, giúp tiết kiệm bộ nhớ và tăng tốc độ dự đoán
                logits = self.model(x) # hàm này sẽ truyền tensor x qua mô hình để nhận được các logits, đây là các giá trị chưa được chuẩn hóa đại diện cho xác suất của mỗi lớp
                prods = torch.softmax(logits, dim = -1).numpy()[0]  # hàm này sẽ áp dụng hàm softmax lên các logits để chuyển chúng thành xác suất, sau đó chuyển kết quả thành một mảng NumPy và lấy phần tử đầu tiên (vì chúng ta chỉ có một mẫu trong batch)
            idx = int(np.argmax(prods)) # hàm này sẽ tìm chỉ số của lớp có xác suất cao nhất trong mảng prods
            return {
                "action": self.labels[idx], # trả về nhãn của lớp có xác suất cao nhất
                "confidence": float(prods[idx]), # trả về xác suất của lớp đó dưới dạng
                "probability": dict(zip(self.labels, prods.tolist())) # trả về xác suất của tất cả các lớp dưới dạng một danh sách
            }
    def _default_model_path()-> str: 
        configured = os.getenv("MODEL_PATH") # hàm này sẽ lấy giá trị của biến môi trường MODEL_PATH, nếu biến này không được thiết lập thì sẽ trả về None
        if configured and Path(configured).is_file(): # nếu biến môi trường được thiết lập và đường dẫn đến tệp tin là hợp lệ
            return configured # trả về đường dẫn đã được cấu hình
        base_dir = Path(__file__).resolve().parents[2]
        return str(base_dir / "models" / "lstmcnn.pt")
    def _default_feature_dim() -> int:
        return int(os.getenv("FEATURE_DIM", "30")) # hàm này sẽ lấy giá trị của biến môi trường FEATURE_DIM, nếu biến này không được thiết lập thì sẽ trả về giá trị mặc định là 9, sau đó chuyển đổi giá trị đó thành một số nguyên và trả về nó

mode_service = ModelService(
    model_path = ModelService._default_model_path(),
    feature_dim = ModelService._default_feature_dim()
)