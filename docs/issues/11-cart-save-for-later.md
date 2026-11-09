---
id: 11-cart-save-for-later
title: "cart: salvar para depois"
depends: [10-cart-items]
provides: [backend/app/modules/cart/service.py]
context_files: [backend/app/modules/cart/service.py, backend/app/modules/cart/router.py, backend/tests/conftest.py, backend/tests/test_issue_11_cart_save_for_later.py]
test_cmd: cd backend && python -m pytest tests/test_issue_11_cart_save_for_later.py tests/test_issue_10_cart_items.py -q
max_iters: 4
---
# cart: salvar para depois

Os testes estão em `backend/tests/test_issue_11_cart_save_for_later.py` e **não podem ser
alterados**. Os testes da issue 10 precisam continuar passando.

## Novas funções em `cart/service.py`

- `save_for_later(session, user_id, product_id) -> CartView`: move o item para
  `saved_for_later`, mantendo a quantidade. Ele deixa de contar em `item_count` e `total_cents`.
- `move_to_cart(session, user_id, product_id) -> CartView`: volta para `items`.

As duas dão `NotFoundError` se o produto não está no carrinho e são idempotentes (salvar o que já
está salvo não é erro).

## Novos endpoints (Bearer, só o dono)

- `POST /api/cart/{user_id}/items/{product_id}/save-for-later` → **200** com o carrinho
- `POST /api/cart/{user_id}/items/{product_id}/move-to-cart` → **200** com o carrinho
