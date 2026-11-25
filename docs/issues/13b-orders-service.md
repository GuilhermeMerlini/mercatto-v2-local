---
id: 13b-orders-service
title: "orders: service de checkout (parte 2 da issue 13)"
depends: [07-catalog-stock, 12-payments-mock, 13a-orders-models-delivery]
provides: [backend/app/modules/orders/service.py]
context_files: [backend/app/core/errors.py, backend/app/core/clock.py, backend/app/modules/orders/models.py, backend/tests/conftest.py, backend/tests/test_issue_13_orders_checkout.py]
test_cmd: cd backend && python -m pytest tests/test_issue_13_orders_checkout.py -q -k "service_ or gateway_exception or before_charge"
max_iters: 4
---
# orders: service de checkout (parte 2 da issue 13)

Testes: `-k "service_ or gateway_exception or before_charge"` (não podem ser alterados). Altere
somente `orders/service.py`; `models.py` e `delivery.py` já estão prontos. Implemente **todas**
as regras abaixo: os testes HTTP da parte 3 também as verificam.

## Tipos

Reexporte os enums de `models.py`. Dataclasses congeladas: `Address(full_name, street, city,
state, zip)`, `CheckoutItem(product_id, quantity)`, `OrderItemView(id, product_id, seller_id,
quantity, unit_price_cents)` e `OrderView` (`id`, `buyer_id`, `status`, `fulfillment_status`,
`total_cents`, `address: Address`, `shipping_method`, `payment_method`,
`items: list[OrderItemView]`, `created_at`, `paid_at`, `shipped_at`, `out_for_delivery_at`,
`delivered_at`, `estimated_delivery_date` = `delivery.estimate(paid_at or created_at, ...)`).

## checkout(session, buyer_id, items, address, shipping_method, payment_method, idempotency_key=None) -> OrderView

1. Com `idempotency_key` não vazia e pedido do comprador com essa chave → devolve esse pedido.
2. Lista vazia, `quantity < 1` ou campo de endereço vazio/só espaços → `InvalidInputError`.
   Produto repetido vira um item com as quantidades somadas. Produto inexistente → `NotFoundError`.
3. Reserva com `catalog.decrease_stock` antes de cobrar. Se **qualquer** reserva falhar, devolve
   o já reservado com `increase_stock` e propaga. Nenhum pedido é criado.
4. Cria o pedido `PROCESSING` com os itens (`seller_id` e `unit_price_cents` do produto) e
   `total_cents`, e faz `commit`. Se der `IntegrityError` (mesma chave em paralelo): `rollback`,
   devolve o estoque e retorna o pedido existente.
5. `payments.charge(order.id, total_cents, "USD")`: aprovado → `PAID` com `paid_at` e
   `payment_transaction_id`; recusado → `FAILED` e devolve o estoque (não é exceção); exceção →
   `FAILED` com `commit`, devolve o estoque e propaga.
