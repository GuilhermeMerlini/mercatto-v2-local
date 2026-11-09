from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.deps import get_current_user
from app.core.db import get_session
from app.modules.users.schemas import UserRegisterInput, UserLoginInput, UserOutput, TokenOutput
from app.modules.users.service import register_user, authenticate_user
from app.core.security import create_access_token
from app.core.errors import ConflictError, NotFoundError, AuthenticationError
from app.modules.users.models import User

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserRegisterInput, session: Session = Depends(get_session)) -> UserOutput:
    try:
        user = register_user(session, data)
        return UserOutput.model_validate(user)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login")
def login(data: UserLoginInput, session: Session = Depends(get_session)) -> TokenOutput:
    try:
        user = authenticate_user(session, data)
        token = create_access_token(user.id)
        return TokenOutput(access_token=token)
    except (NotFoundError, AuthenticationError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> UserOutput:
    return UserOutput.model_validate(current_user)
