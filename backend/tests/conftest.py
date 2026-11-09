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

BUYER = {"name": "Ana", "email": "ana@example.com", "password": "S3nha-forte!", "role": "BUYER"}
SELLER = {"name": "Bruno", "email": "bruno@example.com", "password": "S3nha-forte!", "role": "SELLER"}


def _register_models() -> None:
    try:
        import app.modules.registry  # noqa: F401  (existe a partir da issue 02)
    except ImportError:
        pass


@pytest.fixture(name="engine")
def engine_fixture():
    _register_models()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def register(client, user: dict | None = None, **overrides):
    return client.post("/api/users/register", json={**(user or BUYER), **overrides})


def login(client, email: str, password: str):
    return client.post("/api/users/login", json={"email": email, "password": password})


def auth_headers(client, user: dict | None = None) -> dict[str, str]:
    """Cadastra o usuário (se ainda não existe), faz login e devolve o header Authorization."""
    user = user or BUYER
    register(client, user)
    r = login(client, user["email"], user["password"])
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------- helpers usados a partir da issue 05 ----------

SELLER_2 = {"name": "Carla", "email": "carla@example.com", "password": "S3nha-forte!", "role": "SELLER"}
BUYER_2 = {"name": "Davi", "email": "davi@example.com", "password": "S3nha-forte!", "role": "BUYER"}

PRODUCT = {
    "name": "Notebook Aurora 14",
    "description": "Notebook leve com 16 GB de RAM",
    "price_cents": 450000,
    "stock": 5,
    "category": "Eletrônicos",
    "brand": "Aurora",
}

ADDRESS = {
    "full_name": "Ana Souza",
    "street": "Rua das Flores, 100",
    "city": "Porto Alegre",
    "state": "RS",
    "zip": "90000-000",
}


def login_user(client, user: dict) -> tuple[dict[str, str], int]:
    """Cadastra (se preciso) e loga. Devolve (headers, id)."""
    register(client, user)
    r = login(client, user["email"], user["password"])
    assert r.status_code == 200, r.text
    return bearer(r.json()["access_token"]), r.json()["id"]


def create_product(client, headers, **overrides) -> dict:
    r = client.post("/api/catalog/products", json={**PRODUCT, **overrides}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def checkout(client, headers, cart_items, key: str | None = None, **overrides):
    """cart_items: lista de (product_id, quantity). overrides substituem campos do corpo."""
    body = {
        "items": [{"product_id": pid, "quantity": q} for pid, q in cart_items],
        "address": ADDRESS,
        "shipping_method": "STANDARD",
        "payment_method": "CARD",
        **overrides,
    }
    extra = {"Idempotency-Key": key} if key else {}
    return client.post("/api/orders/checkout", json=body, headers={**headers, **extra})


@pytest.fixture(autouse=True)
def _reset_payment_gateway():
    """Cada teste começa com o gateway mock aprovando tudo (existe a partir da issue 12)."""
    yield
    try:
        from app.modules.payments import service as payments
    except ImportError:
        return
    payments.set_gateway(payments.MockPaymentGateway("none"))


@pytest.fixture(name="sql_log")
def sql_log_fixture(engine):
    """Lista dos SQLs executados no engine de teste (para checar UPDATEs atômicos)."""
    from sqlalchemy import event

    statements: list[str] = []

    def capture(conn, cursor, statement, *args):
        statements.append(" ".join(statement.split()))

    event.listen(engine, "before_cursor_execute", capture)
    yield statements
    event.remove(engine, "before_cursor_execute", capture)
