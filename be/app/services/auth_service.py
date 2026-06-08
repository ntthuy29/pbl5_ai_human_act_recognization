import hashlib
import hmac
import os
import re

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest
from app.core.auth import Auth 
from fastapi import HTTPException, Depends, status

class AuthService:
    def get_user_by_email(self, email: str, db):
        normalized_email = email.strip().lower()
        return db.execute(
            select(User).where(User.email == normalized_email)
        ).scalar_one_or_none()
    def get_me(self, user_id: int, db):
        return db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

    def register(self, payload: RegisterRequest):
        normalized_email = payload.email.strip().lower()

        if not self._is_valid_email(normalized_email):
            raise ValueError("INVALID_EMAIL")

        if payload.password != payload.confirm_password:
            raise ValueError("PASSWORDS_DO_NOT_MATCH")

        if len(payload.password) < 8:
            raise ValueError("WEAK_PASSWORD")

        with SessionLocal() as db:
            if self.get_user_by_email(normalized_email, db):
                raise ValueError("EMAIL_ALREADY_REGISTERED")

            user = User(
                email=normalized_email,
                full_name=payload.full_name.strip() if payload.full_name else None,
                password_hash=self._hash_password(payload.password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return {
                "id": user.id,
                "email": user.email,
            }

    def login(self, email: str, password: str):
        normalized_email = email.strip().lower()

        if not self._is_valid_email(normalized_email):
            raise ValueError("INVALID_EMAIL")

        with SessionLocal() as db:
            user = self.get_user_by_email(normalized_email, db)
            if not user:
                raise ValueError("INVALID_CREDENTIALS")

            if not self._verify_password(password, user.password_hash):
                raise ValueError("INVALID_CREDENTIALS")
            auth= Auth()
            access_token = auth.create_access_token(
                data = {
                    "user_id": user.id,
                    "email": user.email
                },
                expires_delta=None
            )

            return {
                    "access_token": access_token,
                    "user": {
                        "user_id": user.id,
                        "email": user.email,
                    }
            
            }
            

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"{salt.hex()}:{hashed.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt_hex, hash_hex = stored_hash.split(":", 1)
        except ValueError:
            return False

        try:
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)
        except ValueError:
            return False

        computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(computed_hash, expected_hash)

    def _is_valid_email(self, email: str) -> bool:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return re.match(pattern, email) is not None


auth_service = AuthService()
