from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.deps import AuthUser, get_current_user
from app.core.security import create_access_token
from app.modules.users.schemas import (
    LoginIn,
    LoginOut,
    PasswordChangeIn,
    ProfileUpdateIn,
    RegisterIn,
    UserOut,
)
from app.modules.users.service import authenticate, change_password, get_user, register, update_profile

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterIn, session: Session = Depends(get_session)):
    return register(session, body.name, body.email, body.password, body.role)

@router.post("/login", response_model=LoginOut)
def login_user(body: LoginIn, session: Session = Depends(get_session)):
    user = authenticate(session, body.email, body.password)
    token, expires_at = create_access_token(user.id, user.role)
    return LoginOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        access_token=token,
        token_type="bearer",
        expires_at=expires_at
    )

@router.get("/me", response_model=UserOut)
def get_me(auth: AuthUser = Depends(get_current_user),
           session: Session = Depends(get_session)):
    return get_user(session, auth.id)

@router.patch("/me", response_model=UserOut)
def update_me(body: ProfileUpdateIn, auth: AuthUser = Depends(get_current_user),
              session: Session = Depends(get_session)):
    return update_profile(session, auth.id, name=body.name, email=body.email)

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password_endpoint(body: PasswordChangeIn, auth: AuthUser = Depends(get_current_user),
                            session: Session = Depends(get_session)):
    change_password(session, auth.id, body.current_password, body.new_password)

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, auth: AuthUser = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    auth.require_owner(user_id)
    return get_user(session, user_id)
