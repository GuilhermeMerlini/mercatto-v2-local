---
id: 03b-users-router
title: "users: rotas de cadastro e login (parte 2 da issue 03)"
depends: [01-core-auth, 02-app-wiring, 03a-users-model-service]
provides: [backend/app/modules/users/schemas.py, backend/app/modules/users/router.py]
context_files: [backend/app/main.py, backend/app/core/db.py, backend/app/core/security.py, backend/tests/conftest.py, backend/tests/test_issue_03_users_register_login.py]
test_cmd: cd backend && python -m pytest tests/test_issue_03_users_register_login.py -q -k "not service and not table"
max_iters: 4
---
# users: rotas de cadastro e login (parte 2 da issue 03)

Os testes estão em `backend/tests/test_issue_03_users_register_login.py` e **não podem ser
alterados**. Esta parte cobre os testes HTTP (`-k "not service and not table"`).

O `service.py` de users **já está pronto** (parte 1, `03a`); a API dele aparece em
"API PÚBLICA DAS DEPENDÊNCIAS". Use essas funções como estão: **não reescreva `service.py` nem
`models.py`** e não altere nada em `backend/app/core/`.

Altere somente `backend/app/modules/users/schemas.py`, `backend/app/modules/users/router.py` e
`backend/app/main.py`.

## schemas.py

Modelos Pydantic de entrada e saída do HTTP (o `UserView` **não** fica aqui, ele é do service):

- `RegisterIn`: `name` (não vazio), `email` (`EmailStr`), `password` (8 a 72 caracteres),
  `role` (`Literal["BUYER", "SELLER"]`, padrão `"BUYER"`). Entrada inválida ou campo faltando
  já vira **422** pelo próprio FastAPI.
- `LoginIn`: `email`, `password`.
- `UserOut`: `id, name, email, role, created_at` (exatamente esses campos).
- `LoginOut`: os campos de `UserOut` + `access_token`, `token_type`, `expires_at`.

## router.py

`router = APIRouter(prefix="/api/users", tags=["users"])`, registrado em `main.py` com
`app.include_router(...)`.

A sessão do banco vem de `get_session` (`core/db.py`) via `Depends`, e é passada como
**primeiro argumento** das funções do service:
`def register_user(body: RegisterIn, session: Session = Depends(get_session))`.

- `POST /register` `{name, email, password, role?}` → **201** com `UserOut`.
  Email duplicado → **409**.
- `POST /login` `{email, password}` → **200**
  `{id, name, email, role, created_at, access_token, token_type: "bearer", expires_at}`.
  Credenciais erradas → **401**. O token é criado com
  `token, expires_at = create_access_token(user.id, user.role)`.

## Regras

- Não use `try/except` nem `HTTPException` no router: os erros do service (`ConflictError`,
  `AuthenticationError`, ...) sobem sozinhos e o handler de `main.py` converte em 409/401.
- Senha nunca aparece em resposta.
