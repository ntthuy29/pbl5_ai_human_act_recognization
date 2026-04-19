from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

SECRET_KEY = "pbl5_secret_key"
ALGORITHM = "HS256" # thuật toán dùng để mã hóa và giải mã token
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class Auth: 
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) 
            # dòng này là để đảm bảo rằng thời gian hết hạn của token được tính toán dựa trên thời gian hiện tại ở múi giờ UTC, giúp tránh các vấn đề liên quan đến múi giờ khi xác thực token. 
    # #Nếu không có expires_delta được cung cấp, token sẽ mặc định hết hạn sau 60 phút.
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_access_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload #hàm này để trả payload ( tức là dữ liệu đã được mã hóa trong token - thường là thông tin người dùng) 
        except JWTError:
            return None