from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.core.db import get_session
from app.modules.users.service import register, authenticate
from app.modules.users.schemas import RegisterIn, LoginIn, UserOut, LoginOut
from sqlalchemy.orm import Session
from app.core.security import create_access_token

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
