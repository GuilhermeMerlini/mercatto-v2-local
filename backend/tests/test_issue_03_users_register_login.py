import ast
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from tests.conftest import BUYER, SELLER, login, register

USERS = Path(__file__).resolve().parent.parent / "app" / "modules" / "users"
USER_FIELDS = {"id", "name", "email", "role", "created_at"}


# ---------- cadastro ----------


def test_register_success(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert isinstance(body["id"], int)
    assert body["name"] == "Ana"
    assert body["email"] == "ana@example.com"
    assert body["role"] == "BUYER"


def test_register_returns_exactly_public_fields(client):
    body = register(client).json()
    assert set(body) == USER_FIELDS
    assert BUYER["password"] not in str(body)


def test_register_created_at_is_utc(client):
    created_at = datetime.fromisoformat(register(client).json()["created_at"].replace("Z", "+00:00"))
    assert created_at.utcoffset().total_seconds() == 0


def test_register_role_defaults_to_buyer(client):
    body = {k: v for k, v in BUYER.items() if k != "role"}
    r = client.post("/api/users/register", json=body)
    assert r.status_code == 201
    assert r.json()["role"] == "BUYER"


def test_register_seller(client):
    r = register(client, SELLER)
    assert r.status_code == 201
    assert r.json()["role"] == "SELLER"


def test_register_normalizes_email(client):
    r = register(client, email="  Ana@Example.COM ")
    assert r.status_code == 201
    assert r.json()["email"] == "ana@example.com"


def test_register_duplicate_email_returns_409(client):
    assert register(client).status_code == 201
    r = register(client, name="Outra Ana")
    assert r.status_code == 409
    assert "detail" in r.json()


def test_register_duplicate_email_ignores_case(client):
    assert register(client).status_code == 201
    assert register(client, email="ANA@example.com").status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "isso-nao-e-email"},
        {"password": "curta"},
        {"password": "a" * 73},
        {"role": "ADMIN"},
        {"name": ""},
    ],
)
def test_register_invalid_input_returns_422(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_register_missing_field_returns_422(client):
    assert client.post("/api/users/register", json={"email": "x@example.com"}).status_code == 422


def test_password_is_not_stored_in_plain_text(client, session):
    register(client)
    rows = session.execute(text('SELECT * FROM "user"')).fetchall()
    assert len(rows) == 1
    assert BUYER["password"] not in [str(v) for v in rows[0]]


# ---------- login ----------


def test_login_success_returns_token_and_user(client):
    register(client)
    r = login(client, BUYER["email"], BUYER["password"])
    assert r.status_code == 200
    body = r.json()
    assert set(body) == USER_FIELDS | {"access_token", "token_type", "expires_at"}
    assert body["token_type"] == "bearer"
    assert body["email"] == "ana@example.com"
    assert body["access_token"]


def test_login_token_carries_id_and_role(client):
    from app.core.security import decode_access_token

    user_id = register(client, SELLER).json()["id"]
    token = login(client, SELLER["email"], SELLER["password"]).json()["access_token"]
    assert decode_access_token(token) == (user_id, "SELLER")


def test_login_email_ignores_case(client):
    register(client)
    assert login(client, "ANA@EXAMPLE.COM", BUYER["password"]).status_code == 200


def test_login_wrong_password_returns_401(client):
    register(client)
    r = login(client, BUYER["email"], "senha-errada")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_login_unknown_email_returns_401_with_same_message(client):
    register(client)
    wrong_password = login(client, BUYER["email"], "senha-errada").json()
    unknown_email = login(client, "ninguem@example.com", BUYER["password"]).json()
    assert unknown_email == wrong_password


def test_login_missing_field_returns_422(client):
    assert client.post("/api/users/login", json={"email": "x@example.com"}).status_code == 422


# ---------- service e estrutura ----------


def test_service_register_and_authenticate(session):
    from app.core.errors import AuthenticationError, ConflictError, InvalidInputError
    from app.modules.users import service

    user = service.register(session, "Ana", "ana@example.com", "S3nha-forte!")
    assert (user.name, user.email, user.role) == ("Ana", "ana@example.com", "BUYER")
    assert service.authenticate(session, "ana@example.com", "S3nha-forte!").id == user.id
    with pytest.raises(ConflictError):
        service.register(session, "Ana", "ana@example.com", "S3nha-forte!")
    with pytest.raises(InvalidInputError):
        service.register(session, "Bia", "bia@example.com", "curta")
    with pytest.raises(AuthenticationError):
        service.authenticate(session, "ana@example.com", "errada!!")


def test_service_get_and_find_user(session):
    from app.core.errors import NotFoundError
    from app.modules.users import service

    user = service.register(session, "Ana", "ana@example.com", "S3nha-forte!")
    assert service.get_user(session, user.id) == user
    assert service.find_user(session, user.id) == user
    assert service.find_user(session, 999) is None
    with pytest.raises(NotFoundError):
        service.get_user(session, 999)


def test_service_returns_frozen_dataclass_not_orm(session):
    import dataclasses

    from app.modules.users import service

    user = service.register(session, "Ana", "ana@example.com", "S3nha-forte!")
    assert dataclasses.is_dataclass(user)
    assert not hasattr(user, "hashed_password")
    with pytest.raises(dataclasses.FrozenInstanceError):
        user.name = "outra"


def test_user_table_is_registered():
    import app.modules.registry  # noqa: F401

    assert "user" in SQLModel.metadata.tables


def test_service_does_not_import_fastapi():
    tree = ast.parse((USERS / "service.py").read_text())
    imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imported += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(m.split(".")[0] in {"fastapi", "starlette"} for m in imported)


def test_router_does_not_raise_http_exception():
    assert "HTTPException" not in (USERS / "router.py").read_text()
