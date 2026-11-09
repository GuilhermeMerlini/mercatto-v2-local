from sqlmodel import Session, select
from app.core.errors import ConflictError, NotFoundError, AuthenticationError
from app.modules.users.models import User
from app.modules.users.schemas import UserRegisterInput, UserLoginInput
from app.core.security import hash_password, verify_password


def register_user(session: Session, data: UserRegisterInput) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email já cadastrado")

    hashed = hash_password(data.password)
    user = User(email=data.email, name=data.name, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, data: UserLoginInput) -> User:
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise NotFoundError("Usuário não encontrado")

    if not verify_password(data.password, user.hashed_password):
        raise AuthenticationError("Senha incorreta")

    return user
