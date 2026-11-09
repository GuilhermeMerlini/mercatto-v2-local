import os

# Antes de importar a app: segredo fixo e banco em memória (nenhum arquivo .db é criado).
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from sqlmodel.pool import StaticPool  # noqa: E402

from app.core.db import get_session  # noqa: E402
from app.main import app  # noqa: E402

DEFAULT_USER = {"email": "ana@example.com", "password": "S3nha-forte!", "name": "Ana"}


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_auth_headers(client: TestClient, user: dict | None = None) -> dict[str, str]:
    """Cadastra o usuário, faz login e devolve o header Authorization."""
    user = user or DEFAULT_USER
    client.post("/users/register", json=user)
    r = client.post("/users/login", json={"email": user["email"], "password": user["password"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client):
    return make_auth_headers(client)
