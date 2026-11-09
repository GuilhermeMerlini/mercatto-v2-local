---
id: 01-core-auth
title: "Core: hash de senha, JWT e usuário autenticado"
depends: []
provides: [backend/app/core/security.py, backend/app/core/deps.py]
context_files: [backend/app/core/config.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/tests/test_issue_01_core_auth.py]
test_cmd: cd backend && python -m pytest tests/test_issue_01_core_auth.py -q
max_iters: 4
---
# Core: hash de senha, JWT e usuário autenticado

Os testes estão em `backend/tests/test_issue_01_core_auth.py` e **não podem ser alterados**.

## Criar `backend/app/core/security.py`

- `hash_password(password: str) -> str` — bcrypt via `passlib` (`CryptContext(schemes=["bcrypt"])`).
- `verify_password(password: str, hashed: str) -> bool` — senha com mais de 72 bytes (UTF-8)
  devolve `False` sem chamar o bcrypt.
- `BCRYPT_MAX_BYTES = 72`
- `create_access_token(user_id: int, role: str) -> tuple[str, datetime]` — JWT HS256 (`python-jose`)
  com `sub` = `str(user_id)`, `role` e `exp`. Devolve `(token, expires_at)`; `expires_at` em UTC
  (`clock.utcnow()` + `config.ACCESS_TOKEN_EXPIRE_MINUTES`). Segredo: `config.JWT_SECRET`
  (leia `config.JWT_SECRET` na hora de usar, não copie para uma constante no import).
- `decode_access_token(token: str) -> tuple[int, str]` — devolve `(user_id, role)`. Token
  inválido, expirado, com outra assinatura ou sem `sub`/`role` → `AuthenticationError`.

## Criar `backend/app/core/deps.py`

- `AuthUser` — `@dataclass(frozen=True)` com `id: int` e `role: str`, e os métodos:
  - `require_role(role)` → `ForbiddenError` se `self.role != role`
  - `require_owner(owner_id)` → `ForbiddenError` se `self.id != owner_id`
- `get_current_user(credentials = Depends(HTTPBearer(auto_error=False))) -> AuthUser`
  — sem credenciais → `AuthenticationError`; senão decodifica o token. **Não consulta o banco.**

## Regras

- Nada aqui importa `app.modules`.
- Não lance `HTTPException`: use as exceções de `app/core/errors.py`.
