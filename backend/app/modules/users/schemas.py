from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLoginInput(BaseModel):
    email: EmailStr
    password: str


class UserOutput(BaseModel):
    id: int
    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
