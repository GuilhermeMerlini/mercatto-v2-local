---
id: 04-users-profile
title: "users: perfil (/me) e troca de senha"
depends: [03-users-register-login]
provides: [backend/app/modules/users/service.py]
context_files: [backend/app/core/deps.py, backend/app/core/errors.py, backend/app/core/security.py, backend/app/modules/users/models.py, backend/app/modules/users/schemas.py, backend/app/modules/users/service.py, backend/app/modules/users/router.py, backend/tests/conftest.py, backend/tests/test_issue_04_users_profile.py]
test_cmd: cd backend && python -m pytest tests/test_issue_04_users_profile.py tests/test_issue_03_users_register_login.py -q
max_iters: 4
---
# users: perfil (/me) e troca de senha

Os testes estão em `backend/tests/test_issue_04_users_profile.py` e **não podem ser alterados**.
Os testes da issue 03 precisam continuar passando. Pré-requisito: issue 03.

## Novas funções em `users/service.py`

- `update_profile(session, user_id, name=None, email=None) -> UserView` — `None` não altera o
  campo. Nome vazio/só espaços → `InvalidInputError`. Email normalizado (minúsculas, sem espaços
  nas pontas); email já usado por **outro** usuário → `ConflictError` (o próprio email pode ser
  reenviado). Usuário inexistente → `NotFoundError`.
- `change_password(session, user_id, current_password, new_password) -> None` — senha atual
  errada → `InvalidInputError` (400, **nunca** 401: o front deslogaria o usuário). Nova senha com
  menos de 8 caracteres ou mais de 72 bytes, ou igual à atual → `InvalidInputError`.

## Novos endpoints (todos exigem Bearer; sem token ou token inválido → **401**)

Use `AuthUser = Depends(get_current_user)` de `core/deps.py`.

- `GET /api/users/me` → **200** `{id, name, email, role, created_at}`
- `PATCH /api/users/me` `{name?, email?}` → **200** usuário atualizado. `email` com formato
  inválido ou `name` vazio → **422**; email de outro usuário → **409**.
- `PUT /api/users/me/password` `{current_password, new_password}` → **204** sem corpo.
  Senha atual errada ou nova senha igual à atual → **400**; `new_password` fora de 8..72 → **422**.
- `GET /api/users/{user_id}` → **200** se `user_id` é o do token; outro usuário → **403**
  (`auth.require_owner(user_id)`).

Declare as rotas `/me` **antes** de `/{user_id}` no router.
