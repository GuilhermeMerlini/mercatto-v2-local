---
id: 19-seed
title: "Seed: usuários e produtos de exemplo"
depends: [03-users-register-login, 05-catalog-crud]
provides: []
context_files: [backend/app/core/db.py, backend/tests/conftest.py, backend/tests/test_issue_19_seed.py]
test_cmd: cd backend && python -m pytest tests/test_issue_19_seed.py -q
max_iters: 4
---
# Seed: usuários e produtos de exemplo

Os testes estão em `backend/tests/test_issue_19_seed.py` e **não podem ser alterados**.

O CSV `backend/app/seed_data/products.csv` já existe, com 500 produtos e as colunas
`name,price,stock_quantity,category,image_url`. O preço está em reais com ponto decimal
(`13.20`).

## Criar `backend/app/seed.py`

- `seed(session, limit: int | None = None) -> dict`
  1. Se já existe algum usuário com email `@mercatto.dev`, não faz nada e devolve
     `{"users": 0, "products": 0}` (idempotente).
  2. Cria, via `users.service.register` e com a senha `mercatto123`:
     - os vendedores `seller1@mercatto.dev` e `seller2@mercatto.dev`;
     - o comprador `buyer@mercatto.dev`.
  3. Lê o CSV com o módulo `csv` (os nomes têm vírgulas entre aspas) e cria os produtos via
     `catalog.service.create_product`:
     - `price_cents = round(Decimal(price) * 100)`;
     - `brand` = primeira palavra do nome;
     - os produtos são distribuídos entre os 2 vendedores em rodízio;
     - linhas com preço inválido ou `<= 0` são puladas.
     - `limit` limita a quantidade de produtos.
  4. Devolve `{"users": 3, "products": <quantos criou>}`.
- `if __name__ == "__main__":` roda `init_db()` e `seed()` com uma sessão do `engine` e imprime
  o resultado. Uso: `cd backend && python -m app.seed`.

Use só `users.service` e `catalog.service`: o seed não importa `models` de módulos.
