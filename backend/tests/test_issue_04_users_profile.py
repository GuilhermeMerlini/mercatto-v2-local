import pytest

from tests.conftest import BUYER, SELLER, auth_headers, bearer, login, register

PUBLIC_FIELDS = {"id", "name", "email", "role", "created_at"}


# ---------- GET /me ----------


def test_me_returns_current_user(client):
    headers = auth_headers(client)
    r = client.get("/api/users/me", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == PUBLIC_FIELDS
    assert body["email"] == BUYER["email"]


def test_me_for_seller(client):
    r = client.get("/api/users/me", headers=auth_headers(client, SELLER))
    assert r.json()["role"] == "SELLER"


@pytest.mark.parametrize("headers", [{}, bearer("token-invalido"), {"Authorization": "Basic abc"}])
def test_me_without_valid_token_returns_401(client, headers):
    assert client.get("/api/users/me", headers=headers).status_code == 401


# ---------- PATCH /me ----------


def test_patch_name_only(client):
    headers = auth_headers(client)
    r = client.patch("/api/users/me", json={"name": "Ana Maria"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Ana Maria"
    assert r.json()["email"] == BUYER["email"]


def test_patch_email_is_normalized_and_login_uses_new_email(client):
    headers = auth_headers(client)
    r = client.patch("/api/users/me", json={"email": " Nova@Example.com "}, headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "nova@example.com"
    assert login(client, "nova@example.com", BUYER["password"]).status_code == 200
    assert login(client, BUYER["email"], BUYER["password"]).status_code == 401


def test_patch_empty_body_changes_nothing(client):
    headers = auth_headers(client)
    before = client.get("/api/users/me", headers=headers).json()
    r = client.patch("/api/users/me", json={}, headers=headers)
    assert r.status_code == 200
    assert r.json() == before


def test_patch_own_email_again_is_ok(client):
    headers = auth_headers(client)
    assert client.patch("/api/users/me", json={"email": BUYER["email"]}, headers=headers).status_code == 200


def test_patch_email_of_another_user_returns_409(client):
    register(client, SELLER)
    headers = auth_headers(client)
    r = client.patch("/api/users/me", json={"email": "BRUNO@example.com"}, headers=headers)
    assert r.status_code == 409


@pytest.mark.parametrize("body", [{"email": "nao-e-email"}, {"name": ""}])
def test_patch_invalid_input_returns_422(client, body):
    assert client.patch("/api/users/me", json=body, headers=auth_headers(client)).status_code == 422


def test_patch_blank_name_is_rejected(client):
    r = client.patch("/api/users/me", json={"name": "   "}, headers=auth_headers(client))
    assert r.status_code in (400, 422)


def test_patch_without_token_returns_401(client):
    assert client.patch("/api/users/me", json={"name": "X"}).status_code == 401


# ---------- PUT /me/password ----------


def change_password(client, headers, current, new):
    return client.put(
        "/api/users/me/password",
        json={"current_password": current, "new_password": new},
        headers=headers,
    )


def test_change_password_success(client):
    headers = auth_headers(client)
    r = change_password(client, headers, BUYER["password"], "Nova-s3nha!")
    assert r.status_code == 204
    assert r.content == b""
    assert login(client, BUYER["email"], "Nova-s3nha!").status_code == 200
    assert login(client, BUYER["email"], BUYER["password"]).status_code == 401


def test_change_password_wrong_current_returns_400_not_401(client):
    headers = auth_headers(client)
    r = change_password(client, headers, "senha-errada", "Nova-s3nha!")
    assert r.status_code == 400
    assert login(client, BUYER["email"], BUYER["password"]).status_code == 200


def test_change_password_same_as_current_returns_400(client):
    headers = auth_headers(client)
    assert change_password(client, headers, BUYER["password"], BUYER["password"]).status_code == 400


@pytest.mark.parametrize("new", ["curta", "a" * 73])
def test_change_password_invalid_new_returns_422(client, new):
    assert change_password(client, auth_headers(client), BUYER["password"], new).status_code == 422


def test_change_password_without_token_returns_401(client):
    r = client.put("/api/users/me/password", json={"current_password": "a" * 8, "new_password": "b" * 8})
    assert r.status_code == 401


# ---------- GET /{id} ----------


def test_get_own_user_by_id(client):
    headers = auth_headers(client)
    me = client.get("/api/users/me", headers=headers).json()
    r = client.get(f"/api/users/{me['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json() == me


def test_get_other_user_by_id_returns_403(client):
    other_id = register(client, SELLER).json()["id"]
    assert client.get(f"/api/users/{other_id}", headers=auth_headers(client)).status_code == 403


def test_get_user_by_id_without_token_returns_401(client):
    assert client.get("/api/users/1").status_code == 401


# ---------- service ----------


def test_service_update_profile_and_change_password(session):
    from app.core.errors import ConflictError, InvalidInputError, NotFoundError
    from app.modules.users import service

    ana = service.register(session, "Ana", "ana@example.com", "S3nha-forte!")
    service.register(session, "Bruno", "bruno@example.com", "S3nha-forte!")

    assert service.update_profile(session, ana.id).name == "Ana"
    assert service.update_profile(session, ana.id, name="Ana M.").name == "Ana M."
    with pytest.raises(ConflictError):
        service.update_profile(session, ana.id, email="bruno@example.com")
    with pytest.raises(InvalidInputError):
        service.update_profile(session, ana.id, name="  ")
    with pytest.raises(NotFoundError):
        service.update_profile(session, 999, name="X")

    with pytest.raises(InvalidInputError):
        service.change_password(session, ana.id, "errada!!", "Nova-s3nha!")
    service.change_password(session, ana.id, "S3nha-forte!", "Nova-s3nha!")
    assert service.authenticate(session, "ana@example.com", "Nova-s3nha!").id == ana.id
