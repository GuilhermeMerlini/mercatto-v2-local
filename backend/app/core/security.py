from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core import config, clock
from app.core.errors import AuthenticationError

BCRYPT_MAX_BYTES = 72

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return crypt_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode('utf-8')) > BCRYPT_MAX_BYTES:
        return False
    return crypt_context.verify(password, hashed)

def create_access_token(user_id: int, role: str) -> tuple[str, datetime]:
    current_time = clock.utcnow()
    expires_at = current_time + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": int(expires_at.timestamp())
    }
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token, expires_at

def decode_access_token(token: str) -> tuple[int, str]:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        if "sub" not in payload or "role" not in payload:
            raise AuthenticationError("Missing required claims")
        try:
            user_id = int(payload["sub"])
        except ValueError:
            raise AuthenticationError("Invalid sub claim")
        role = payload["role"]
        if "exp" not in payload:
            raise AuthenticationError("Missing exp claim")
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if exp_time < clock.utcnow():
            raise AuthenticationError("Token expired")
        return user_id, role
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")
    except KeyError as e:
        raise AuthenticationError(f"Missing claim: {e}")
