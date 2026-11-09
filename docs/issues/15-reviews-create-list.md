---
id: 15-reviews-create-list
title: "reviews: criar e listar avaliações, atualizando a nota do produto"
depends: [07-catalog-stock, 03-users-register-login]
provides: [backend/app/modules/reviews/service.py]
context_files: [backend/app/main.py, backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/app/core/deps.py, backend/tests/conftest.py, backend/tests/test_issue_15_reviews_create_list.py]
test_cmd: cd backend && python -m pytest tests/test_issue_15_reviews_create_list.py -q
max_iters: 4
---
# reviews: criar e listar avaliações, atualizando a nota do produto

Os testes estão em `backend/tests/test_issue_15_reviews_create_list.py` e **não podem ser
alterados**.

## Criar `backend/app/modules/reviews/{models,schemas,service,router}.py`

**models.py**: tabela `Review` com `id`, `product_id` (indexado), `author_id`, `stars` (1..5),
`title`, `text` (opcional), `helpful_count` (padrão 0) e `created_at` (UTC). Acrescente o import
em `modules/registry.py`.

**service.py**

- `ReviewView`: dataclass congelada com `id`, `product_id`, `author_id`, `author_name`, `stars`,
  `title`, `text`, `helpful_count` e `created_at`. `author_name` vem de
  `users.service.find_user`. Usuário inexistente ou com nome vazio → `"Usuário"`.
- `RatingAggregate`: dataclass congelada com `product_id`, `average_rating` (2 casas; 0.0 sem
  avaliações) e `review_count`.
- `create_review(session, product_id, author_id, stars, title, text=None) -> ReviewView`
  - `stars` fora de 1..5 ou título vazio → `InvalidInputError`.
  - Produto inexistente → `NotFoundError`, via `catalog.service.get_product`.
  - Depois de salvar, recalcula o agregado e chama `catalog.service.update_rating`.
- `list_by_product(session, product_id) -> list[ReviewView]`: mais recentes primeiro (empate:
  maior id primeiro). Produto sem avaliações → `[]`.
- `get_aggregate(session, product_id) -> RatingAggregate`

**router.py**: registrar em `main.py` com o prefixo `/api/reviews`.

- `GET /products/{product_id}` (público) → **200** lista
- `POST /products/{product_id}` (Bearer) `{stars, title, text?}` → **201** com a avaliação.
  - `stars` fora de 1..5, título vazio ou com mais de 255 caracteres, ou `text` com mais de
    2000 → **422**.
  - Produto inexistente → **404**.
