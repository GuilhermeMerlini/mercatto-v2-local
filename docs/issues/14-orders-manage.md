---
id: 14-orders-manage
title: "orders: consulta, troca de endereço e nova tentativa de pagamento"
depends: [13-orders-checkout]
provides: [backend/app/modules/orders/service.py]
context_files: [backend/app/modules/orders/models.py, backend/app/modules/orders/schemas.py, backend/app/modules/orders/service.py, backend/app/modules/orders/router.py, backend/app/core/errors.py, backend/tests/conftest.py, backend/tests/test_issue_14_orders_manage.py]
test_cmd: cd backend && python -m pytest tests/test_issue_14_orders_manage.py tests/test_issue_13_orders_checkout.py -q
max_iters: 5
---
# orders: consulta, troca de endereço e nova tentativa de pagamento

Os testes estão em `backend/tests/test_issue_14_orders_manage.py` e **não podem ser alterados**.
Os testes da issue 13 precisam continuar passando.

## Novas funções em `orders/service.py`

Em todas, pedido inexistente → `NotFoundError` e pedido de outro comprador → `ForbiddenError`.

- `get_order(session, order_id, buyer_id) -> OrderView`
- `list_by_buyer(session, buyer_id) -> list[OrderView]`: mais recentes primeiro (empate: maior
  id primeiro).
- `update_shipping_address(session, order_id, buyer_id, address) -> OrderView`
  - Campo vazio → `InvalidInputError`.
  - Pedido `CANCELLED`, ou com `fulfillment_status` diferente de `NOT_SHIPPED` → `ConflictError`.
- `retry_payment(session, order_id, buyer_id, payment_method) -> OrderView`
  - Só pedidos `FAILED`; outros → `ConflictError`.
  - "Reivindica" o pedido com um `UPDATE` condicional (`WHERE status = 'FAILED'` → `PROCESSING`,
    gravando o novo `payment_method`). Se nenhuma linha mudou, outra requisição chegou antes →
    `ConflictError`.
  - Reserva o estoque de novo, como no checkout. Se faltar, volta para `FAILED` e propaga
    `InsufficientStockError`.
  - Cobra como no checkout: aprovado → `PAID`; recusado → `FAILED` e devolve o estoque.

## Novos endpoints (Bearer)

- `GET /api/orders` → **200** lista dos pedidos do usuário do token
- `GET /api/orders/{id}` → **200** / **403** / **404**
- `PATCH /api/orders/{id}/address` `{full_name, street, city, state, zip}` → **200** / **409**.
  Campo vazio → **422**.
- `POST /api/orders/{id}/payment` `{payment_method}` → **200** com o pedido (`PAID` ou `FAILED`).
  Pedido não `FAILED` → **409**. Sem estoque → **409**.
