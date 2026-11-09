# ARCHITECTURE

Monolito modular em Python + FastAPI. Um processo, um banco SQLite, SQLModel.

## Estrutura

```text
backend/app/
├── core/                # infraestrutura compartilhada (sem regra de negócio)
│   ├── config.py        # variáveis de ambiente (JWT_SECRET, DATABASE_URL, CORS_ORIGINS...)
│   ├── db.py            # engine, get_session, init_db, tipo UTCDateTime
│   ├── errors.py        # exceções de domínio (cada uma tem status_code)
│   ├── clock.py         # utcnow()
│   ├── security.py      # hash de senha + JWT
│   └── deps.py          # AuthUser, get_current_user
├── modules/<nome>/
│   ├── models.py        # tabelas SQLModel (privado do módulo)
│   ├── schemas.py       # Pydantic de entrada/saída da API (privado do módulo)
│   ├── service.py       # regras de negócio — ÚNICA API pública do módulo
│   └── router.py        # endpoints FastAPI; só valida, autoriza e chama o service
├── modules/registry.py  # importa os models de todos os módulos (para init_db)
└── main.py              # registra routers, handler de erros e CORS
backend/tests/test_issue_<NN>_<slug>.py
```

Módulos: users, catalog, search, cart, orders, payments, reviews, sellers.

## Regras

1. Um módulo usa outro SOMENTE via `app.modules.<outro>.service`. Nunca importar
   `models`, `schemas` ou `router` de outro módulo.
2. Dependências permitidas (sem ciclos):
   catalog → users · search → catalog · cart → catalog · orders → catalog, payments ·
   reviews → catalog, users · sellers → catalog, orders · payments → (nada).
3. Referência entre módulos é por id (int), nunca `relationship` do ORM.
4. `service.py` não importa FastAPI. Recebe `session: Session` como 1º argumento, faz
   `commit` e devolve dataclasses (`@dataclass(frozen=True)`), não objetos do ORM.
5. Erros de negócio: o service lança exceções de `app/core/errors.py`
   (`NotFoundError`, `ConflictError`, `AuthenticationError`, `ForbiddenError`,
   `InvalidInputError`, `InsufficientStockError`). O handler global em `main.py` as traduz
   para HTTP; routers não lançam `HTTPException`.
6. IDs inteiros, datas em UTC com tzinfo (`clock.utcnow()`, coluna `UTCDateTime`),
   dinheiro em centavos (`int`, campos terminados em `_cents`).
7. Todas as rotas ficam sob `/api/<módulo>`. Erro sempre no formato `{"detail": "..."}`.
8. Autenticação: `Authorization: Bearer <jwt>`. O token carrega `sub` (id) e `role`
   (`BUYER` | `SELLER`); `get_current_user` não consulta o banco.

## Front

`frontend/` em React + TS (Vite). Tipos da API gerados com `openapi-typescript` a partir de
`/openapi.json`. Não escrever tipos de API à mão.
