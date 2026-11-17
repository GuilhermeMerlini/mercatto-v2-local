from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal["BUYER", "SELLER"] = "BUYER"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

class LoginOut(UserOut):
    access_token: str
    token_type: str
    expires_at: datetime

class ProfileUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None

class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)
