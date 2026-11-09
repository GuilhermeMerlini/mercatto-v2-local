---
id: 01-core-users
context_files: [backend/app/main.py, backend/app/core/db.py, backend/app/core/errors.py, backend/tests/conftest.py, backend/tests/test_users.py]
test_cmd: cd backend && python -m pytest tests/test_users.py -q
max_iters: 4
---
# Core + módulo users

Os testes já existem em `backend/tests/test_users.py` e **não podem ser alterados**.
Implemente o código para que passem.

Criar:

- `backend/app/core/security.py`: hash de senha (passlib bcrypt) e JWT (python-jose). Segredo vem da env `JWT_SECRET`.
- `backend/app/modules/users/{__init__,models,schemas,service,router}.py`.
- `backend/app/core/deps.py`: dependência `get_current_user` (lê `Authorization: Bearer <token>`, devolve o usuário; token ausente ou inválido → 401). Será reutilizada por outros módulos.
- Registrar o router em `backend/app/main.py` com prefixo `/users`.

Modelo: classe `User` (tabela `user`) com `id`, `email` (único), `name`, `hashed_password`.

Endpoints:

- `POST /users/register` {email (formato de email válido), password, name} → **201** `{id, email, name}` (exatamente esses 3 campos). Email duplicado → **409**.
- `POST /users/login` {email, password} → **200** `{access_token, token_type: "bearer"}`. Email inexistente ou senha errada → **401**.
- `GET /users/me` (Bearer) → **200** `{id, email, name}`. Sem token ou token inválido → **401**.

Regras:

- `service.py` não importa FastAPI. Erros de negócio vêm de `app/core/errors.py` (`ConflictError` etc.); o router converte em HTTP.
- Senha nunca é retornada nem guardada em texto puro.
