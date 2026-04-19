from fastapi import APIRouter, HTTPException, status

from app.schemas.auth_schema import (
    LoginData,
    LoginRequest,
    LoginResponse,
    RegisterData,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
)
def register(payload: RegisterRequest):
    try:
        user = auth_service.register(payload)
    except ValueError as exc:
        error_code = str(exc)
        if error_code == "EMAIL_ALREADY_REGISTERED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        if error_code == "PASSWORDS_DO_NOT_MATCH":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
        if error_code == "INVALID_EMAIL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
        if error_code == "WEAK_PASSWORD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid registration data")

    return RegisterResponse(
        success=True,
        data=RegisterData(user_id=user["id"], email=user["email"]),
    )


@router.post(
    "/auth/login",
    response_model=LoginResponse,
)
def login(payload: LoginRequest):
    try:
        user = auth_service.login(payload.email, payload.password)
        print(user)
    except ValueError as exc:
        error_code = str(exc)
        if error_code == "INVALID_EMAIL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
        if error_code == "INVALID_CREDENTIALS":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login data")

    return LoginResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        data=LoginData(user_id=user["user"]["user_id"], email=user["user"]["email"], access_token=user["access_token"]),
    )