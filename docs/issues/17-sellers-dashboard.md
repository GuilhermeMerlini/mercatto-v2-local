---
id: 17-sellers-dashboard
title: "sellers: inventário, pedidos recebidos, envio e métricas"
depends: [06-catalog-read, 14-orders-manage]
provides: [backend/app/modules/sellers/service.py, backend/app/modules/orders/service.py]
context_files: [backend/app/main.py, backend/app/core/errors.py, backend/app/core/deps.py, backend/app/modules/orders/models.py, backend/app/modules/orders/service.py, backend/tests/conftest.py, backend/tests/test_issue_17_sellers_dashboard.py]
test_cmd: cd backend && python -m pytest tests/test_issue_17_sellers_dashboard.py tests/test_issue_14_orders_manage.py -q
max_iters: 5
---
# sellers: inventário, pedidos recebidos, envio e métricas

Os testes estão em `backend/tests/test_issue_17_sellers_dashboard.py` e **não podem ser
alterados**. Os testes da issue 14 precisam continuar passando.

## Novas funções em `orders/service.py`

- `list_by_seller(session, seller_id) -> list[OrderView]`: pedidos com ao menos um item do
  vendedor, mais recentes primeiro. A view traz **todos** os itens do pedido.
- `advance_fulfillment(session, order_id, seller_id, target: FulfillmentStatus) -> OrderView`
  - Pedido inexistente → `NotFoundError`.
  - Vendedor sem itens no pedido → `ForbiddenError`.
  - Pedido não `PAID` → `ConflictError`.
  - `target` precisa ser exatamente o próximo passo de
    `NOT_SHIPPED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED`; pular ou voltar → `ConflictError`.
  - Grava a data correspondente: `shipped_at`, `out_for_delivery_at` ou `delivered_at`.

## Criar `backend/app/modules/sellers/{service,schemas,router}.py`

Sem tabelas: só compõe `catalog.service` e `orders.service`.

**service.py**
- `SellerOrderItemView(product_id, quantity, unit_price_cents)`
- `SellerOrderView`: `id`, `buyer_id`, `status`, `fulfillment_status`, `created_at`,
  `items` (**só os itens deste vendedor**) e `subtotal_cents` (soma desses itens).
- `SellerMetrics`: `total_revenue_cents` (soma dos `subtotal_cents` dos pedidos `PAID`) e
  `low_stock_products` (produtos do vendedor com `stock < 10`).
- `get_inventory(session, seller_id, page, page_size)`: delega a
  `catalog.service.list_by_seller`.
- `get_received_orders(session, seller_id) -> list[SellerOrderView]`
- `advance_fulfillment(session, seller_id, order_id, target: str) -> SellerOrderView`: converte
  `target` para `FulfillmentStatus`. Valor inválido → `InvalidInputError`.
- `get_metrics(session, seller_id) -> SellerMetrics`

**router.py**: registrar em `main.py` com o prefixo `/api/sellers`. Todas as rotas exigem Bearer
de `SELLER` **e** `seller_id` igual ao do token (senão **403**).

- `GET /{seller_id}/products?page=&page_size=` → **200** `{items, total, page, page_size}`
- `GET /{seller_id}/orders` → **200** lista de `SellerOrderView`
- `GET /{seller_id}/metrics` → **200**
- `POST /{seller_id}/orders/{order_id}/fulfillment` `{status}` → **200**. Transição inválida ou
  pedido não pago → **409**. Status fora de `SHIPPED`, `OUT_FOR_DELIVERY` e `DELIVERED` → **422**.

`sellers/schemas.py` define os próprios formatos (não importa schemas/models de outros módulos).
Os status saem como string.
