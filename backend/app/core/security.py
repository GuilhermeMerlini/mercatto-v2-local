from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core import config, clock
from app.core.errors import AuthenticationError, InvalidInputError

BCRYPT_MAX_BYTES = 72

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise InvalidInputError("Password exceeds maximum allowed bytes")
    return crypt_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        return False
    return crypt_context.verify(password, hashed)

def create_access_token(user_id: int, role: str) -> tuple[str, datetime]:
    expires_at = clock.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at.replace(tzinfo=None)
    }
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token, expires_at

def decode_access_token(token: str) -> tuple[int, str]:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        if "sub" not in payload or "role" not in payload:
            raise AuthenticationError("Missing required claims in token")
        user_id = int(payload["sub"])
        role = payload["role"]
        return user_id, role
    except (JWTError, ValueError, TypeError): # linha editada manualmente
        raise AuthenticationError("Invalid or expired token")
