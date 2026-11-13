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

O `service.py` e o `models.py` de users **já estão prontos** (parte 1, `03a`); a API do service
aparece em "API PÚBLICA DAS DEPENDÊNCIAS". Use essas funções como estão: **não reescreva
`service.py` nem `models.py`** e não altere nada em `backend/app/core/`.

Altere somente `backend/app/modules/users/schemas.py`, `backend/app/modules/users/router.py` e
`backend/app/main.py`.

## main.py

Mantenha o `main.py` como está e acrescente **apenas** estas duas linhas (o import junto dos
outros imports, o `include_router` depois da criação do `app`):

```python
from app.modules.users.router import router as users_router

app.include_router(users_router)
```

Não registre routers de outros módulos (`catalog`, `cart`, `orders`, ...): eles ainda não
existem e o import quebra a aplicação. Não use `from app.modules import users` + `users.router`:
importar o pacote não carrega o submódulo `router`.

## schemas.py

Modelos Pydantic de entrada e saída do HTTP. O `UserView` **não** fica aqui (ele é do service)
e o `UserRole` **não** é redefinido aqui:

```python
from typing import Literal
from pydantic import BaseModel, EmailStr, Field
```

- `RegisterIn`:
  - `name: str = Field(min_length=1)`
  - `email: EmailStr`
  - `password: str = Field(min_length=8, max_length=72)`
  - `role: Literal["BUYER", "SELLER"] = "BUYER"`
- `LoginIn`: `email: EmailStr`, `password: str`.
- `UserOut`: `id: int`, `name: str`, `email: str`, `role: str`, `created_at: datetime`
  (exatamente esses campos).
- `LoginOut(UserOut)`: + `access_token: str`, `token_type: str`, `expires_at: datetime`.

Entrada inválida ou campo faltando vira **422** sozinho, pela validação do FastAPI.

## router.py

`router = APIRouter(prefix="/api/users", tags=["users"])`.

A sessão do banco vem de `get_session` (`core/db.py`) via `Depends`, e é passada como
**primeiro argumento** das funções do service:
`def register_user(body: RegisterIn, session: Session = Depends(get_session))`.

- `POST /register` `{name, email, password, role?}` → **201** com `UserOut`. O status vai no
  decorator: `@router.post("/register", response_model=UserOut, status_code=201)`.
  Email duplicado → **409** (o service já lança `ConflictError`).
- `POST /login` `{email, password}` → **200** com `LoginOut`:
  `{id, name, email, role, created_at, access_token, token_type: "bearer", expires_at}`.
  O token é criado com `token, expires_at = create_access_token(user.id, user.role)`.
  Credenciais erradas → **401** (o service já lança `AuthenticationError`).

## Regras

- **Sem `try/except`, sem `JSONResponse` e sem `HTTPException` no router.** Os erros do service
  (`ConflictError`, `AuthenticationError`, ...) sobem sozinhos e o handler que já existe em
  `main.py` converte em 409/401 com o corpo certo. Cada endpoint é só: chamar o service e
  devolver o resultado.
- Senha nunca aparece em resposta.
