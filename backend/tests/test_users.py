from sqlalchemy import text

from tests.conftest import DEFAULT_USER


def register(client, **overrides):
    return client.post("/users/register", json={**DEFAULT_USER, **overrides})


def login(client, **overrides):
    body = {"email": DEFAULT_USER["email"], "password": DEFAULT_USER["password"], **overrides}
    return client.post("/users/login", json=body)


# ---------- register ----------


def test_register_success(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert isinstance(body["id"], int)
    assert body["email"] == DEFAULT_USER["email"]
    assert body["name"] == DEFAULT_USER["name"]


def test_register_never_returns_password(client):
    body = register(client).json()
    assert set(body.keys()) == {"id", "email", "name"}
    assert DEFAULT_USER["password"] not in str(body)


def test_register_duplicate_email_returns_409(client):
    assert register(client).status_code == 201
    assert register(client, name="Outra Ana").status_code == 409


def test_register_invalid_email_returns_422(client):
    assert register(client, email="isso-nao-e-email").status_code == 422


def test_register_missing_field_returns_422(client):
    r = client.post("/users/register", json={"email": "x@example.com"})
    assert r.status_code == 422


def test_password_is_not_stored_in_plain_text(client, session):
    register(client)
    rows = session.execute(text('SELECT * FROM "user"')).fetchall()
    assert len(rows) == 1
    assert DEFAULT_USER["password"] not in [str(v) for v in rows[0]]


# ---------- login ----------


def test_login_success_returns_bearer_token(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_wrong_password_returns_401(client):
    register(client)
    assert login(client, password="senha-errada").status_code == 401


def test_login_unknown_email_returns_401(client):
    assert login(client, email="ninguem@example.com").status_code == 401


# ---------- me ----------


def test_me_returns_current_user(client):
    created = register(client).json()
    token = login(client).json()["access_token"]
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == created


def test_me_without_token_returns_401(client):
    assert client.get("/users/me").status_code == 401


def test_me_with_invalid_token_returns_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer token.invalido.aqui"})
    assert r.status_code == 401


def test_tokens_identify_different_users(client):
    register(client)
    register(client, email="bob@example.com", name="Bob")
    t_bob = login(client, email="bob@example.com").json()["access_token"]
    r = client.get("/users/me", headers={"Authorization": f"Bearer {t_bob}"})
    assert r.json()["email"] == "bob@example.com"
