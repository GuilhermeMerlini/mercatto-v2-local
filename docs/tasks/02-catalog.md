---
id: 02-catalog
context_files: [backend/app/main.py, backend/app/core/db.py, backend/app/core/deps.py, backend/app/core/errors.py, backend/app/modules/users/service.py, backend/tests/conftest.py, backend/tests/test_catalog.py]
test_cmd: cd backend && python -m pytest tests/test_catalog.py -q
max_iters: 4
---
# Módulo catalog (produtos, categorias, estoque)

Os testes já existem em `backend/tests/test_catalog.py` e **não podem ser alterados**.
Pré-requisito: tarefa 01 concluída (`get_current_user` em `app/core/deps.py`).

Criar `backend/app/modules/catalog/{__init__,models,schemas,service,router}.py` e registrar o
router em `main.py` com prefixo `/catalog`.

Modelos: `Category(id, name)`, `Product(id, name, description, price_cents, stock, category_id, seller_id)`.
Referências por id (int), sem `relationship`.

Endpoints:

- `POST /catalog/categories` (Bearer) {name} → **201** `{id, name}`
- `GET /catalog/categories` → **200** lista de `{id, name}` (público)
- `POST /catalog/products` (Bearer) {name, description, price_cents, stock, category_id} → **201**
  com `{id, name, description, price_cents, stock, category_id, seller_id}`.
  `seller_id` = id do usuário do token. `price_cents >= 0` e `stock >= 0` (senão **422**).
  `category_id` inexistente → **404**. Sem token → **401**.
- `GET /catalog/products/{id}` → **200** (mesmo formato acima) ou **404**
- `GET /catalog/products?category_id=&page=1&page_size=20` → **200**
  `{items: [...], total, page, page_size}`. `page >= 1`, `page_size >= 1` (senão **422**).
  `category_id` filtra. Ordem estável por `id`.

Funções públicas em `service.py` (recebem `session` como primeiro argumento, fazem `commit`):

- `get_product(session, product_id) -> Product`; inexistente → `NotFoundError`
- `decrease_stock(session, product_id, qty) -> None`; produto inexistente → `NotFoundError`;
  `qty > stock` → `InsufficientStockError` (estoque permanece intacto); `qty == stock` é permitido.

Erros de domínio vêm de `app/core/errors.py`. O router os converte em HTTP (404 / 409).
`service.py` não importa FastAPI.
