from dataclasses import dataclass
from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends
from jose import jwt
from app.core import config, clock
from app.core.errors import AuthenticationError, ForbiddenError

@dataclass(frozen=True)
class AuthUser:
    id: int
    role: str
    
    def require_role(self, role: str) -> None:
        if self.role != role:
            raise ForbiddenError("Forbidden: insufficient permissions")
    
    def require_owner(self, owner_id: int) -> None:
        if self.id != owner_id:
            raise ForbiddenError("Forbidden: not owner")

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends()) -> AuthUser:
    if not credentials:
        raise AuthenticationError("Missing credentials")
    try:
        token = credentials.credentials
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        if "sub" not in payload or "role" not in payload:
            raise AuthenticationError("Missing required claims")
        try:
            user_id = int(payload["sub"])
        except ValueError:
            raise AuthenticationError("Invalid sub claim")
        role = payload["role"]
        return AuthUser(id=user_id, role=role)
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")
    except KeyError as e:
        raise Authentication
