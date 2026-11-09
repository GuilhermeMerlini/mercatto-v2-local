import ast
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.core import config, deps, security
from app.core.clock import utcnow
from app.core.errors import AuthenticationError, ForbiddenError

CORE = Path(__file__).resolve().parent.parent / "app" / "core"


def creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# ---------- senha ----------


def test_hash_is_not_the_password_and_verifies():
    hashed = security.hash_password("S3nha-forte!")
    assert hashed != "S3nha-forte!"
    assert security.verify_password("S3nha-forte!", hashed)
    assert not security.verify_password("outra-senha", hashed)


def test_same_password_hashes_differently():
    assert security.hash_password("S3nha-forte!") != security.hash_password("S3nha-forte!")


def test_password_over_72_bytes_never_verifies():
    hashed = security.hash_password("a" * 72)
    assert security.BCRYPT_MAX_BYTES == 72
    assert not security.verify_password("a" * 72 + "b", hashed)
    assert not security.verify_password("é" * 40, hashed)  # 80 bytes em UTF-8


# ---------- JWT ----------


def test_token_roundtrip_returns_id_and_role():
    token, _ = security.create_access_token(42, "SELLER")
    assert security.decode_access_token(token) == (42, "SELLER")


def test_token_payload_has_sub_as_string_and_role():
    token, _ = security.create_access_token(7, "BUYER")
    payload = jwt.get_unverified_claims(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "BUYER"
    assert "exp" in payload


def test_expires_at_is_utc_and_matches_config():
    before = utcnow()
    _, expires_at = security.create_access_token(1, "BUYER")
    assert expires_at.tzinfo is not None
    expected = before + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    assert abs((expires_at - expected).total_seconds()) < 5


def test_tampered_token_is_rejected():
    token, _ = security.create_access_token(1, "BUYER")
    with pytest.raises(AuthenticationError):
        security.decode_access_token(token[:-2] + ("AA" if not token.endswith("AA") else "BB"))


def test_garbage_token_is_rejected():
    with pytest.raises(AuthenticationError):
        security.decode_access_token("isso-nao-e-um-jwt")


def test_token_signed_with_other_secret_is_rejected():
    forged = jwt.encode({"sub": "1", "role": "SELLER", "exp": utcnow() + timedelta(hours=1)},
                        "outro-segredo", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        security.decode_access_token(forged)


def test_expired_token_is_rejected():
    expired = jwt.encode({"sub": "1", "role": "BUYER", "exp": utcnow() - timedelta(minutes=1)},
                         config.JWT_SECRET, algorithm="HS256")
    with pytest.raises(AuthenticationError):
        security.decode_access_token(expired)


@pytest.mark.parametrize("claims", [{"role": "BUYER"}, {"sub": "1"}, {"sub": "abc", "role": "BUYER"}])
def test_token_without_valid_sub_or_role_is_rejected(claims):
    token = jwt.encode({**claims, "exp": utcnow() + timedelta(hours=1)}, config.JWT_SECRET, algorithm="HS256")
    with pytest.raises(AuthenticationError):
        security.decode_access_token(token)


def test_secret_is_read_from_config_at_call_time(monkeypatch):
    monkeypatch.setattr(config, "JWT_SECRET", "segredo-trocado")
    token, _ = security.create_access_token(1, "BUYER")
    assert security.decode_access_token(token) == (1, "BUYER")
    monkeypatch.setattr(config, "JWT_SECRET", "test-secret")
    with pytest.raises(AuthenticationError):
        security.decode_access_token(token)


# ---------- deps ----------


def test_auth_user_require_role():
    user = deps.AuthUser(id=1, role="BUYER")
    user.require_role("BUYER")
    with pytest.raises(ForbiddenError):
        user.require_role("SELLER")


def test_auth_user_require_owner():
    user = deps.AuthUser(id=1, role="BUYER")
    user.require_owner(1)
    with pytest.raises(ForbiddenError):
        user.require_owner(2)


def test_auth_user_is_immutable():
    user = deps.AuthUser(id=1, role="BUYER")
    with pytest.raises(Exception):
        user.id = 2


def test_get_current_user_from_valid_token():
    token, _ = security.create_access_token(9, "SELLER")
    assert deps.get_current_user(creds(token)) == deps.AuthUser(id=9, role="SELLER")


def test_get_current_user_without_credentials_raises():
    with pytest.raises(AuthenticationError):
        deps.get_current_user(None)


def test_get_current_user_with_invalid_token_raises():
    with pytest.raises(AuthenticationError):
        deps.get_current_user(creds("invalido"))


@pytest.mark.parametrize("filename", ["security.py", "deps.py"])
def test_core_does_not_import_modules_or_raise_http_exception(filename):
    source = (CORE / filename).read_text()
    tree = ast.parse(source)
    imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imported += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(m.startswith("app.modules") for m in imported)
    assert "HTTPException" not in source
