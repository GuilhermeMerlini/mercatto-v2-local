---
id: 03a-users-model-service
title: "users: model e service (parte 1 da issue 03)"
depends: [01-core-auth, 02-app-wiring]
provides: [backend/app/modules/users/models.py, backend/app/modules/users/service.py]
context_files: [backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/app/core/security.py, backend/tests/conftest.py, backend/tests/test_issue_03_users_register_login.py]
test_cmd: cd backend && python -m pytest tests/test_issue_03_users_register_login.py -q -k "service or table"
max_iters: 4
---
# users: model e service (parte 1 da issue 03)

Os testes estão em `backend/tests/test_issue_03_users_register_login.py` e **não podem ser
alterados**. Esta parte cobre só os testes de service e da tabela (`-k "service or table"`).
Os testes HTTP (`/register` e `/login`) são da parte 2 (`03b`) e **não** fazem parte desta issue:
não crie `router.py` nem `schemas.py` e não altere `main.py`.

Altere somente `backend/app/modules/users/models.py`, `backend/app/modules/users/service.py` e
`backend/app/modules/registry.py`. Não altere nada em `backend/app/core/`.

## models.py

`UserRole(str, Enum)` com `BUYER` e `SELLER`. Tabela `User` (`__tablename__ = "user"`): `id`,
`name`, `email` (único, indexado), `hashed_password`, `role` (padrão `BUYER`), `created_at`.

`created_at` é anotado como `datetime` (UTC) e usa a coluna `UTCDateTime` do `core/db.py`:
`created_at: datetime = Field(default_factory=utcnow, sa_column=Column(UTCDateTime, nullable=False))`.
`UTCDateTime` é um tipo de coluna do SQLAlchemy, **não** pode ser usado como anotação do campo.

Acrescente `from app.modules.users.models import User  # noqa: F401` em `modules/registry.py`.

## service.py

Define e devolve `UserView` (`@dataclass(frozen=True)`: `id, name, email, role, created_at`;
`role` como `str`). O `UserView` mora **neste arquivo**; nunca devolva o objeto ORM `User`.
Todas as funções recebem a `Session` como primeiro argumento:

- `register(session, name, email, password, role="BUYER") -> UserView`
  — email guardado em minúsculas e sem espaços nas pontas; email já usado (ignorando
  maiúsculas) → `ConflictError`; senha com menos de 8 caracteres ou mais de 72 bytes →
  `InvalidInputError`. Senha guardada só como hash (`hash_password` de `core/security.py`).
- `authenticate(session, email, password) -> UserView` — email (ignorando maiúsculas)
  inexistente ou senha errada → `AuthenticationError` (mesma mensagem nos dois casos;
  use `verify_password`).
- `get_user(session, user_id) -> UserView` — inexistente → `NotFoundError`.
- `find_user(session, user_id) -> UserView | None`

## Regras

- `service.py` não importa FastAPI/Starlette e não lança `HTTPException`; só erros de
  `core/errors.py`.
- Senha nunca é guardada em texto puro.
