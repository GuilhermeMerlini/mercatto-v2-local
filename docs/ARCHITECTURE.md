# ARCHITECTURE

Monolito modular. Um processo, um banco SQLite, SQLModel.

## Estrutura do backend

```text
backend/app/
├── core/          # config.py, db.py, security.py (JWT/hash), deps.py
├── modules/<nome>/
│   ├── models.py    # tabelas SQLModel
│   ├── schemas.py   # Pydantic de entrada/saída
│   ├── service.py   # regras de negócio (ÚNICA API pública do módulo)
│   └── router.py    # endpoints FastAPI, só chama service
└── main.py        # registra os routers
backend/tests/test_<modulo>.py
```

Módulos: users, catalog (inclui estoque), search, cart, orders, payments (mock), reviews.

## Regras

1. Dependências só "para baixo": users ← catalog ← cart ← orders ← payments; reviews → catalog.
2. Um módulo usa outro SOMENTE via `service.py` dele. Nunca importar models/router de outro módulo.
3. Referência entre módulos é por id (int), nunca relationship do ORM.
4. Router não tem regra de negócio; service não importa FastAPI.
5. Pagamento e envio são mocks atrás de uma interface (Protocol).
6. IDs inteiros, datas em UTC, dinheiro em centavos (int).
7. Erros de negócio: lançar `HTTPException` apenas no router; service lança exceções de domínio em `core/errors.py`.

## Front

`frontend/src/{api,features/<modulo>,shared}`. Tipos da API gerados com
`openapi-typescript` a partir de `/openapi.json`. Não escrever tipos de API à mão.
