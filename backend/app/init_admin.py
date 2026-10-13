
import os

from sqlalchemy import select
from pwdlib import PasswordHash

from .database import SessionLocal
from .models import User

password_hash = PasswordHash.recommended()


def main():
    username = os.getenv("INITIAL_ADMIN_USERNAME", "root")
    password = os.getenv("INITIAL_ADMIN_PASSWORD")
    email = os.getenv("INITIAL_ADMIN_EMAIL", "root@usad.local")

    if not password:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD must be set")

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )

        if existing:
            print("Tài khoản username/email đã tồn tại; không thay đổi dữ liệu.")
            return

        user = User(
            username=username,
            email=email,
            password_hash=password_hash.hash(password),
            display_name="USaD Administrator",
            account_status="active",
        )
        db.add(user)
        db.commit()
        print("Đã tạo tài khoản quản trị ban đầu.")


if __name__ == "__main__":
    main()
