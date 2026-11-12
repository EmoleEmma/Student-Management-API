import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import Role, User

email = input("Admin email: ").strip().lower()
password = getpass("Admin password: ")

with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == email)):
        print("User already exists.")
    else:
        db.add(User(email=email, hashed_password=hash_password(password), role=Role.ADMIN))
        db.commit()
        print("Admin created.")