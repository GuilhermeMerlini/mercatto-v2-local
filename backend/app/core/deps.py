from dataclasses import dataclass
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Security
from app.core import config, errors
from app.core.errors import AuthenticationError, ForbiddenError
from app.core.security import decode_access_token

@dataclass(frozen=True)
class AuthUser:
    id: int
    role: str

    def require_role(self, role: str) -> None:
        if self.role != role:
            raise ForbiddenError("User does not have required role")

    def require_owner(self, owner_id: int) -> None:
        if self.id != owner_id:
            raise ForbiddenError("User is not the owner")

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> AuthUser:
    if not credentials:
        raise AuthenticationError("Missing credentials")
    try:
        user_id, role = decode_access_token(credentials.credentials)
        return AuthUser(id=user_id, role=role)
    except AuthenticationError:
        raise AuthenticationError("Invalid token")
