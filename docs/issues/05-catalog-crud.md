---
id: 05-catalog-crud
title: "catalog: produto e CRUD do vendedor"
depends: [01-core-auth, 03-users-register-login]
provides: [backend/app/modules/catalog/service.py]
context_files: [backend/app/main.py, backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/tests/conftest.py, backend/tests/test_issue_05_catalog_crud.py]
test_cmd: cd backend && python -m pytest tests/test_issue_05_catalog_crud.py -q
max_iters: 4
---
# catalog: produto e CRUD do vendedor

Os testes estão em `backend/tests/test_issue_05_catalog_crud.py` e **não podem ser alterados**.

## Criar `backend/app/modules/catalog/{models,schemas,service,router}.py`

**models.py**: tabela `Product` com os campos `id`, `name`, `description` (opcional),
`price_cents` (int), `list_price_cents` (opcional, preço "de", riscado), `stock` (int, padrão 0),
`category` (str, indexado), `image_url`, `brand`, `warranty_months`, `model_number` (todos
opcionais), `seller_id` (int, indexado, **sem** relationship), `average_rating` (float, padrão 0.0),
`review_count` (int, padrão 0) e `created_at` (UTC, como em `users`). Acrescente o import em
`modules/registry.py`.

**service.py**: todos os tipos públicos ficam **neste arquivo**:

- `ProductData`: `@dataclass(frozen=True)` com os campos editáveis. Obrigatórios: `name`,
  `price_cents`, `stock`, `category`. Os demais têm padrão `None`: `description`, `image_url`,
  `brand`, `warranty_months`, `model_number`, `list_price_cents`.
- `ProductView`: `@dataclass(frozen=True)` com **todos** os campos do model.

Funções:

- `create_product(session, seller_id, data: ProductData) -> ProductView`
- `update_product(session, product_id, seller_id, data) -> ProductView`: substitui todos os
  campos editáveis. Produto inexistente → `NotFoundError`. Produto de outro vendedor →
  `ForbiddenError`.
- `delete_product(session, product_id, seller_id) -> None`: mesmos erros do `update_product`.
- `get_product(session, product_id) -> ProductView`: inexistente → `NotFoundError`.
- `find_product(session, product_id) -> ProductView | None`

Validação no service (create e update), com `InvalidInputError`:
- `name`/`category` vazios ou só espaços;
- `price_cents <= 0`;
- `stock < 0`;
- `list_price_cents` informado e `<= price_cents`.

Faça `strip()` em `name` e `category`.

**router.py**: registrar em `main.py` com o prefixo `/api/catalog`.

- `POST /products` (Bearer, só `SELLER`) → **201** com o produto. `seller_id` vem do token.
  Comprador → **403**. Sem token → **401**.
- `GET /products/{id}` (público) → **200** ou **404**.
- `PUT /products/{id}` (Bearer, só `SELLER`, só o dono) → **200**. Inexistente → **404**.
  Dono diferente → **403**.
- `DELETE /products/{id}` (mesmas regras) → **204** sem corpo.

Saída (`ProductOut`): todos os campos do model.

Entrada (`ProductIn`), com 422 automático quando violada:
- `name` 1..255;
- `description` ≤ 2000;
- `price_cents > 0`;
- `list_price_cents > 0` (opcional);
- `stock >= 0`;
- `category` 1..255;
- `image_url` ≤ 1000;
- `brand`/`model_number` ≤ 255;
- `warranty_months >= 0`.

A regra "`list_price_cents` maior que `price_cents`" é do service, então a violação dá **400**.

## Regras

- O papel é checado no router (`auth.require_role("SELLER")`). Ser dono é regra do service.
- `average_rating` e `review_count` não entram em `ProductIn` nem `ProductData`: só a issue 07
  (`update_rating`) os altera.
