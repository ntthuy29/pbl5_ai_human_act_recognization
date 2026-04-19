from pydantic import BaseModel
from datetime import datetime


class RegisterRequest(BaseModel):
    email: str
    password: str
    confirm_password: str
    full_name: str | None = None


class RegisterData(BaseModel):
    user_id: int
    email: str


class RegisterResponse(BaseModel):
    success: bool
    data: RegisterData


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginData(BaseModel):
    access_token: str
    user_id: int
    email: str


class LoginResponse(BaseModel):
    success: bool
    data: LoginData


class MeData(BaseModel):
    user_id: int
    email: str
    full_name: str | None = None
    created_at: datetime


class MeResponse(BaseModel):
    success: bool
    data: MeData
