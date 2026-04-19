from fastapi import APIRouter, HTTPException, Query

from app.db.session import SessionLocal
from app.schemas.auth_schema import MeData, MeResponse
from app.services.auth_service import auth_service
from app.dependencies.auth import get_current_user, get_db

router = APIRouter()


@router.get("/user/me", response_model=MeResponse)
def get_me():
    user = get_current_user()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return MeResponse(
        success=True,
        data=MeData(user_id=user.id, email=user.email, full_name=user.full_name),
    )
    