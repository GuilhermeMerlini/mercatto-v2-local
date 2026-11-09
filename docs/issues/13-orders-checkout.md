---
id: 13-orders-checkout
title: "orders: checkout com reserva de estoque e pagamento"
depends: [07-catalog-stock, 12-payments-mock]
provides: [backend/app/modules/orders/service.py]
context_files: [backend/app/main.py, backend/app/modules/registry.py, backend/app/core/db.py, backend/app/core/errors.py, backend/app/core/clock.py, backend/app/core/deps.py, backend/tests/conftest.py, backend/tests/test_issue_13_orders_checkout.py]
test_cmd: cd backend && python -m pytest tests/test_issue_13_orders_checkout.py -q
max_iters: 5
---
# orders: checkout com reserva de estoque e pagamento

Os testes estão em `backend/tests/test_issue_13_orders_checkout.py` e **não podem ser
alterados**.

## Criar `backend/app/modules/orders/models.py`

Enums (`str, Enum`):
- `OrderStatus`: `PENDING`, `PROCESSING`, `PAID`, `FAILED`, `CANCELLED`
- `FulfillmentStatus`: `NOT_SHIPPED`, `SHIPPED`, `OUT_FOR_DELIVERY`, `DELIVERED`
- `ShippingMethod`: `STANDARD`, `EXPRESS`, `PICKUP`
- `PaymentMethod`: `CARD`, `STORE`, `GIFT`

Tabela `Order` (`__tablename__ = "order"`):
- `id`, `buyer_id` (indexado), `idempotency_key` (opcional);
- `status` (padrão `PENDING`) e `fulfillment_status` (padrão `NOT_SHIPPED`);
- `total_cents`;
- endereço em colunas: `address_full_name`, `address_street`, `address_city`,
  `address_state`, `address_zip`;
- `shipping_method`, `payment_method`, `payment_transaction_id` (opcional);
- datas UTC: `created_at`, mais `paid_at`, `shipped_at`, `out_for_delivery_at` e
  `delivered_at`, todas opcionais.

Unicidade em `(buyer_id, idempotency_key)`.

Tabela `OrderItem` (`__tablename__ = "order_item"`): `id`, `order_id`, `product_id`, `seller_id`,
`quantity` e `unit_price_cents` (o preço **no momento da compra**). Acrescente os imports em
`modules/registry.py`.

## Criar `backend/app/modules/orders/delivery.py`

`estimate(start: datetime | None, method: ShippingMethod) -> date | None`: soma dias úteis (seg a
sex) à data de `start` no fuso `America/Sao_Paulo`. São 1 dia útil para `EXPRESS` e 5 para os
demais. `None` → `None`.

## Criar `backend/app/modules/orders/service.py`

Dataclasses congeladas:
- `Address(full_name, street, city, state, zip)`
- `CheckoutItem(product_id, quantity)`
- `OrderItemView(id, product_id, seller_id, quantity, unit_price_cents)`
- `OrderView` com `id`, `buyer_id`, `status`, `fulfillment_status`, `total_cents`,
  `address: Address`, `shipping_method`, `payment_method`, `items: list[OrderItemView]`,
  `created_at`, `paid_at`, `shipped_at`, `out_for_delivery_at`, `delivered_at` e
  `estimated_delivery_date` (calculada com `delivery.estimate(paid_at or created_at, ...)`).

Reexporte os enums de `models.py`.

`checkout(session, buyer_id, items, address, shipping_method, payment_method, idempotency_key=None)
-> OrderView`:

1. Com `idempotency_key` (não vazia), se já existe pedido do comprador com essa chave, devolve
   esse pedido sem fazer mais nada.
2. Validações:
   - lista vazia, `quantity < 1` ou campo de endereço vazio → `InvalidInputError`;
   - produto inexistente → `NotFoundError`.
   - O mesmo produto repetido na lista vira **um** item com as quantidades somadas.
3. **Reserva o estoque antes de cobrar**, com `catalog.service.decrease_stock` em cada produto.
   Se algum falhar (`InsufficientStockError`), devolve com `increase_stock` o que já tinha sido
   reservado e propaga o erro. Nenhum pedido é criado.
4. Cria o pedido com status `PROCESSING`, os itens (`seller_id` e `unit_price_cents` vêm do
   produto) e `total_cents` = soma de preço × quantidade.
5. Cobra com `payments.service.charge(order.id, total_cents, "BRL")`.
   - **Aprovado** → `PAID`, com `paid_at` e `payment_transaction_id`.
   - **Recusado** → `FAILED` e devolve o estoque. Recusa **não** é exceção: o pedido volta com
     status `FAILED`.
   - Se `charge` lançar exceção → `FAILED`, devolve o estoque e propaga.
6. Concorrência: se dois checkouts com a mesma chave colidirem na unicidade (`IntegrityError`), o
   perdedor faz rollback, devolve o estoque e retorna o pedido do vencedor.

## Criar `orders/schemas.py` e `orders/router.py`

Registrar em `main.py` com o prefixo `/api/orders`.

- `POST /checkout` (Bearer, só `BUYER`; vendedor → **403**). Header opcional `Idempotency-Key`.
  - Corpo: `{items: [{product_id, quantity}], address: {full_name, street, city, state, zip},
    shipping_method, payment_method}`.
  - Resposta **200** com o pedido. Aprovado ou recusado, o status vem no corpo.
  - Lista vazia, campo de endereço vazio/só espaços ou enum inválido → **422**.
  - Produto inexistente → **404**. Estoque insuficiente → **409**.

`OrderOut` tem os mesmos campos de `OrderView`, com `address` aninhado.
