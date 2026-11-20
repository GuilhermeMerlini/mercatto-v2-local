---
id: 13a-orders-models-delivery
title: "orders: models e estimativa de entrega (parte 1 da issue 13)"
depends: [07-catalog-stock, 12-payments-mock]
provides: [backend/app/modules/orders/models.py, backend/app/modules/orders/delivery.py]
context_files: [backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/clock.py, backend/app/modules/catalog/models.py, backend/tests/test_issue_13_orders_checkout.py]
test_cmd: cd backend && python -m pytest tests/test_issue_13_orders_checkout.py -q -k "tables or delivery"
max_iters: 4
---
# orders: models e estimativa de entrega (parte 1 da issue 13)

Testes: `-k "tables or delivery"` (não podem ser alterados). Altere somente `orders/models.py`,
`orders/delivery.py` e `modules/registry.py`.

## models.py

Enums (`str, Enum`): `OrderStatus` (`PENDING`, `PROCESSING`, `PAID`, `FAILED`, `CANCELLED`),
`FulfillmentStatus` (`NOT_SHIPPED`, `SHIPPED`, `OUT_FOR_DELIVERY`, `DELIVERED`),
`ShippingMethod` (`STANDARD`, `EXPRESS`, `PICKUP`), `PaymentMethod` (`CARD`, `STORE`, `GIFT`).

`Order` (`__tablename__ = "order"`): `id`, `buyer_id` (indexado), `idempotency_key` (opcional),
`status` (padrão `PENDING`), `fulfillment_status` (padrão `NOT_SHIPPED`), `total_cents`,
`address_full_name`, `address_street`, `address_city`, `address_state`, `address_zip`,
`shipping_method`, `payment_method`, `payment_transaction_id` (opcional), `created_at` e as
opcionais `paid_at`, `shipped_at`, `out_for_delivery_at`, `delivered_at`. Unicidade em
`(buyer_id, idempotency_key)` com `UniqueConstraint` em `__table_args__`.

Datas como em `catalog/models.py`: `paid_at: datetime | None = Field(default=None, sa_type=UTCDateTime)`.
`UTCDateTime` **não** pode ser a anotação do campo.

`OrderItem` (`__tablename__ = "order_item"`): `id`, `order_id`, `product_id`, `seller_id`,
`quantity`, `unit_price_cents`. Importe `Order` e `OrderItem` em `registry.py`.

## delivery.py

`estimate(start: datetime | None, method: ShippingMethod) -> date | None`: `None` → `None`.
Pega a data de `start.astimezone(ZoneInfo("America/Sao_Paulo"))` (sem subtrair horas na mão) e
soma dias úteis (seg a sex): 1 para `EXPRESS`, 5 para os demais.
