---
id: 10-cart-items
title: "cart: carrinho e itens"
depends: [06-catalog-read]
provides: [backend/app/modules/cart/service.py]
context_files: [backend/app/main.py, backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/app/core/deps.py, backend/tests/conftest.py, backend/tests/test_issue_10_cart_items.py]
test_cmd: cd backend && python -m pytest tests/test_issue_10_cart_items.py -q
max_iters: 4
---
# cart: carrinho e itens

Os testes estão em `backend/tests/test_issue_10_cart_items.py` e **não podem ser alterados**.

## Criar `backend/app/modules/cart/{models,schemas,service,router}.py`

**models.py**: tabela `CartItem` (`__tablename__ = "cart_item"`) com `id`, `user_id` (indexado),
`product_id`, `quantity`, `saved_for_later` (bool, padrão False), `added_at` e `updated_at` (UTC).
Unicidade em `(user_id, product_id)`. Acrescente o import em `modules/registry.py`.

**service.py**: o carrinho **não guarda preço nem nome**. Tudo vem do catálogo na hora
(`catalog.service.get_many`).

- `CartItemView`: `@dataclass(frozen=True)` com `product_id`, `product_name`, `image_url`,
  `unit_price_cents`, `quantity`, `line_total_cents` e `saved_for_later`.
- `CartView`: `@dataclass(frozen=True)` com `user_id`, `items` (fora de "salvar para depois"),
  `saved_for_later` (lista), `item_count` (soma das quantidades de `items`) e `total_cents`
  (soma dos `line_total_cents` de `items`).

As duas listas vêm em ordem de inserção. Item cujo produto não existe mais no catálogo é
omitido da view.

- `get_cart(session, user_id) -> CartView`: carrinho vazio é válido.
- `add_item(session, user_id, product_id, quantity) -> CartView`: produto inexistente →
  `NotFoundError`. Item que já existe **soma** a quantidade (e volta para `items` se estava salvo
  para depois). `quantity < 1` → `InvalidInputError`.
- `update_quantity(session, user_id, product_id, quantity) -> CartView`: item fora do carrinho
  → `NotFoundError`. `quantity < 1` → `InvalidInputError`.
- `remove_item(session, user_id, product_id) -> CartView`: item fora do carrinho →
  `NotFoundError`.
- `clear(session, user_id) -> CartView`

**router.py**: registrar em `main.py` com o prefixo `/api/cart`. Todas as rotas exigem Bearer, e
`user_id` precisa ser o do token (`auth.require_owner(user_id)`; senão **403**).

- `GET /{user_id}` → **200** com o carrinho
- `DELETE /{user_id}` → **200** com o carrinho vazio
- `POST /{user_id}/items` `{product_id, quantity=1}` → **200** com o carrinho
- `PUT /{user_id}/items/{product_id}` `{quantity}` → **200**
- `DELETE /{user_id}/items/{product_id}` → **200**

`quantity < 1` ou `product_id <= 0` no corpo → **422**.
