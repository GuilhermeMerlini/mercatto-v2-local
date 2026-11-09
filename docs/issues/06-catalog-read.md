---
id: 06-catalog-read
title: "catalog: listagem paginada, categorias e consultas para outros módulos"
depends: [05-catalog-crud]
provides: [backend/app/modules/catalog/service.py, backend/app/core/pagination.py]
context_files: [backend/app/modules/catalog/models.py, backend/app/modules/catalog/schemas.py, backend/app/modules/catalog/service.py, backend/app/modules/catalog/router.py, backend/app/core/errors.py, backend/tests/conftest.py, backend/tests/test_issue_06_catalog_read.py]
test_cmd: cd backend && python -m pytest tests/test_issue_06_catalog_read.py tests/test_issue_05_catalog_crud.py -q
max_iters: 4
---
# catalog: listagem paginada, categorias e consultas para outros módulos

Os testes estão em `backend/tests/test_issue_06_catalog_read.py` e **não podem ser alterados**.
Os testes da issue 05 precisam continuar passando.

## Criar `backend/app/core/pagination.py`

`Page(BaseModel, Generic[T])` com `items: list[T]`, `total: int`, `page: int` e `page_size: int`.
`page` começa em 1. Será reutilizado por outros módulos.

## Novas funções em `catalog/service.py`

Toda listagem é ordenada por `id` crescente.

- `list_products(session, category=None, page=1, page_size=20) -> tuple[list[ProductView], int]`:
  devolve a página e o total (já filtrado). `page < 1` ou `page_size < 1` → `InvalidInputError`.
- `list_by_seller(session, seller_id, page=1, page_size=20) -> tuple[list[ProductView], int]`
- `list_categories(session) -> list[str]`: categorias distintas, em ordem alfabética.
- `get_many(session, ids) -> list[ProductView]`: ids desconhecidos são ignorados. Lista vazia
  → `[]`.
- `filter_products(session, category=None, min_price_cents=None, max_price_cents=None,
  min_rating=None) -> list[ProductView]`: todos os produtos que passam nos filtros informados
  (`None` = sem filtro; os limites são inclusivos). É usada pelo módulo search.

## Novos endpoints (públicos)

- `GET /api/catalog/products?category=&page=1&page_size=20` → **200**
  `{items, total, page, page_size}`. `page >= 1` e `1 <= page_size <= 100` (senão **422**).
- `GET /api/catalog/categories` → **200** `["Books", "Toys", ...]`

Declare `GET /products` antes de `GET /products/{id}`.
