from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ConflictError, InvalidInputError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User


@dataclass(frozen=True)
class UserView:
    id: int
    name: str
    email: str
    role: str
    created_at: datetime


def register(session: Session, name: str, email: str, password: str, role: str = "BUYER") -> UserView:
    email = email.strip().lower()
    if session.query(User).filter(User.email == email).first():
        raise ConflictError("Email already registered")

    if len(password.encode("utf-8")) < 8 or len(password.encode("utf-8")) > 72:
        raise InvalidInputError("Password must be between 8 and 72 characters")

    hashed_password = hash_password(password)
    user = User(name=name, email=email, hashed_password=hashed_password, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserView(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def authenticate(session: Session, email: str, password: str) -> UserView:
    email = email.strip().lower()
    user = session.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    return UserView(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def get_user(session: Session, user_id: int) -> UserView:
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return UserView(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def find_user(session: Session, user_id: int) -> Optional[UserView]:
    user = session.get(User, user_id)
    if not user:
        return None
    return UserView(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def update_profile(
    session: Session, user_id: int, name: str | None = None, email: str | None = None
) -> UserView:
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    
    if name is not None:
        if not name.strip():
            raise InvalidInputError("Name cannot be empty or contain only whitespace")
        user.name = name
    
    if email is not None:
        email = email.strip().lower()
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user and existing_user.id != user_id:
            raise ConflictError("Email already registered")
        user.email = email
    
    session.commit()
    session.refresh(user)
    return UserView(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def change_password(session: Session, user_id: int, current_password: str, new_password: str) -> None:
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    
    if not verify_password(current_password, user.hashed_password):
        raise InvalidInputError("Current password is incorrect")
    
    if current_password == new_password:
        raise InvalidInputError("New password must be different from current password")
    
    if len(new_password.encode("utf-8")) < 8 or len(new_password.encode("utf-8")) > 72:
        raise InvalidInputError("New password must be between 8 and 72 characters")
    
    user.hashed_password = hash_password(new_password)
    session.commit()
