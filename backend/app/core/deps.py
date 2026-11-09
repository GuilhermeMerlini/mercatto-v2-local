from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session
from app.core.db import get_session
from app.modules.users.models import User
from app.core.security import SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except JWTError:
        raise credentials_exception

    user = session.get(User, user_id)
    if not user:
        raise credentials_exception
    return user
