from fastapi import Depends, HTTPException, status
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.core.auth import Auth
auth_service = AuthService()

from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
auth = Auth()
def get_db():
    db = SessionLocal()
    try: 
        yield db # cái này sẽ trả về một đối tượng SessionLocal và sau đó tự động đóng kết nối khi xong
    finally:
        db.close()


def get_current_user(token: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db = Depends(get_db)):
    try: 
        payload = auth.decode_access_token(token.credentials)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = auth_service.get_me(user_id=user_id, db=db)
    return user
    