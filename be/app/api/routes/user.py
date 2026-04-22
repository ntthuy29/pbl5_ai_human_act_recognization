from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.schemas.auth_schema import MeData, MeResponse
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/user/me", response_model=MeResponse)
def get_me(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return MeResponse(
        success=True,
        data=MeData(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
        ),
    )
    