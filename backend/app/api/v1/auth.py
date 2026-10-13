
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ...database import get_db
from ...models import User

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()
password_hash = PasswordHash.recommended()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")

JWT_ALGORITHM = "HS256"
TOKEN_HOURS = 8


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=256)


class ChangeAccountRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str | None = Field(default=None, min_length=8, max_length=256)


def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.user_id),
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.account_status != "active":
        raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")
    return user


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or user.account_status != "active":
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    if not password_hash.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "username": user.username,
        "display_name": user.display_name,
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
    }


@router.patch("/account")
def change_account(
    data: ChangeAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not password_hash.verify(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

    existing = db.query(User).filter(
        User.username == data.username,
        User.user_id != user.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã được sử dụng")

    user.username = data.username
    if data.new_password:
        user.password_hash = password_hash.hash(data.new_password)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Không thể cập nhật tài khoản")

    return {"message": "Đã cập nhật tài khoản. Đăng nhập lại nếu cần."}
