import sys

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

import app.modules as app_modules
from app.core import errors
from app.core.db import init_db
from app.main import app

ERRORS = {
    "invalid": (errors.InvalidInputError, 400),
    "auth": (errors.AuthenticationError, 401),
    "forbidden": (errors.ForbiddenError, 403),
    "notfound": (errors.NotFoundError, 404),
    "conflict": (errors.ConflictError, 409),
    "stock": (errors.InsufficientStockError, 409),
}


def _raise(kind: str):
    raise ERRORS[kind][0](f"mensagem {kind}")


if not any(getattr(r, "path", "") == "/_test/error/{kind}" for r in app.routes):
    app.add_api_route("/_test/error/{kind}", _raise, methods=["GET"])


@pytest.fixture(name="raw_client")
def raw_client_fixture():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.mark.parametrize("kind", ERRORS)
def test_domain_error_becomes_http_status_with_detail(raw_client, kind):
    r = raw_client.get(f"/_test/error/{kind}")
    assert r.status_code == ERRORS[kind][1]
    assert r.json() == {"detail": f"mensagem {kind}"}


def test_401_has_www_authenticate_header(raw_client):
    r = raw_client.get("/_test/error/auth")
    assert r.headers.get("www-authenticate") == "Bearer"


def test_other_statuses_have_no_www_authenticate_header(raw_client):
    assert "www-authenticate" not in raw_client.get("/_test/error/notfound").headers


def test_cors_allows_frontend_origin(raw_client):
    r = raw_client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejects_unknown_origin(raw_client):
    r = raw_client.get("/api/health", headers={"Origin": "http://malicioso.example"})
    assert "access-control-allow-origin" not in r.headers


def test_startup_creates_tables(monkeypatch):
    calls = []
    monkeypatch.setattr(SQLModel.metadata, "create_all", lambda *a, **k: calls.append(a))
    with TestClient(app):
        pass
    assert calls, "a subida da app deve chamar init_db() → create_all"


def test_init_db_imports_registry(monkeypatch):
    monkeypatch.setattr(SQLModel.metadata, "create_all", lambda *a, **k: None)
    monkeypatch.delitem(sys.modules, "app.modules.registry", raising=False)
    monkeypatch.delattr(app_modules, "registry", raising=False)
    init_db()
    assert "app.modules.registry" in sys.modules
