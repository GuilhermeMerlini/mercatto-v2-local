---
id: 03-users-register-login
title: "users: cadastro e login"
depends: [01-core-auth, 02-app-wiring]
provides: [backend/app/modules/users/service.py]
context_files: [backend/app/main.py, backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/tests/conftest.py, backend/tests/test_issue_03_users_register_login.py]
test_cmd: cd backend && python -m pytest tests/test_issue_03_users_register_login.py -q
max_iters: 4
---
# users: cadastro e login

Os testes estão em `backend/tests/test_issue_03_users_register_login.py` e **não podem ser
alterados**. Pré-requisito: issues 01 e 02.

## Criar `backend/app/modules/users/{models,schemas,service,router}.py`

**models.py** — `UserRole(str, Enum)` com `BUYER` e `SELLER`. Tabela `User`
(`__tablename__ = "user"`): `id`, `name`, `email` (único, indexado), `hashed_password`,
`role` (padrão `BUYER`), `created_at` (UTC: `Field(default_factory=utcnow,
sa_column=Column(UTCDateTime, nullable=False))`). Acrescente o import em `modules/registry.py`.

**service.py** — devolve `UserView` (`@dataclass(frozen=True)`: `id, name, email, role, created_at`;
`role` como `str`). Funções:

- `register(session, name, email, password, role="BUYER") -> UserView`
  — email guardado em minúsculas e sem espaços nas pontas; email já usado (ignorando
  maiúsculas) → `ConflictError`; senha com menos de 8 caracteres ou mais de 72 bytes →
  `InvalidInputError`. Senha guardada só como hash (`core/security.py`).
- `authenticate(session, email, password) -> UserView` — email (ignorando maiúsculas)
  inexistente ou senha errada → `AuthenticationError` (mesma mensagem nos dois casos).
- `get_user(session, user_id) -> UserView` — inexistente → `NotFoundError`.
- `find_user(session, user_id) -> UserView | None`

**router.py** — registrado em `main.py` com prefixo `/api/users`:

- `POST /register` `{name, email, password, role?}` → **201**
  `{id, name, email, role, created_at}` (exatamente esses campos). `email` inválido, `password`
  fora de 8..72 caracteres, `role` diferente de `BUYER`/`SELLER` ou campo faltando → **422**.
  Email duplicado → **409**.
- `POST /login` `{email, password}` → **200**
  `{id, name, email, role, created_at, access_token, token_type: "bearer", expires_at}`.
  Credenciais erradas → **401**. O token é criado com `create_access_token(user.id, user.role)`.

## Regras

- `service.py` não importa FastAPI e não lança `HTTPException`.
- Senha nunca aparece em resposta nem é guardada em texto puro.
