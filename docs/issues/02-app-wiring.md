---
id: 02-app-wiring
title: "App: handler de erros de domínio, CORS e registro de models"
depends: []
provides: []
context_files: [backend/app/main.py, backend/app/core/config.py, backend/app/core/db.py, backend/app/core/errors.py, backend/tests/test_issue_02_app_wiring.py]
test_cmd: cd backend && python -m pytest tests/test_issue_02_app_wiring.py tests/test_health.py -q
max_iters: 4
---
# App: handler de erros de domínio, CORS e registro de models

Os testes estão em `backend/tests/test_issue_02_app_wiring.py` e **não podem ser alterados**.

## Em `backend/app/main.py`

1. **Handler global** para `DomainError` (de `app/core/errors.py`): responde JSON
   `{"detail": <exc.message>}` com o status `exc.status_code` da própria exceção.
   Para status 401, inclui o header `WWW-Authenticate: Bearer`.
2. **CORS** (`CORSMiddleware`) liberando as origens de `config.CORS_ORIGINS`, todos os
   métodos e headers.
3. **lifespan** que chama `init_db()` na subida da app.
4. Manter `GET /api/health` → `{"status": "ok"}`.

## Criar `backend/app/modules/registry.py`

Arquivo que só importa os `models.py` dos módulos, para o `SQLModel.metadata` conhecer as
tabelas. Por enquanto nenhum módulo tem models: deixe o arquivo só com a docstring. Cada issue
que criar um `models.py` acrescenta uma linha aqui.

## Em `backend/app/core/db.py`

`init_db()` importa `app.modules.registry` (dentro da função) antes de
`SQLModel.metadata.create_all(engine)`.

## Regras

- Routers nunca vão precisar lançar `HTTPException`: o handler cuida disso.
- Não altere `errors.py`.
