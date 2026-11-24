---
id: 14a-orders-read-address
title: "orders: consulta e troca de endereço (parte 1 da issue 14)"
depends: [13-orders-checkout]
provides: [backend/app/modules/orders/service.py, backend/app/modules/orders/router.py]
context_files: [backend/app/modules/orders/schemas.py, backend/app/modules/orders/service.py, backend/app/modules/orders/router.py, backend/app/core/errors.py, backend/tests/test_issue_14_orders_manage.py]
test_cmd: cd backend && python -m pytest tests/test_issue_14_orders_manage.py -q -k "list or get_order or address or service_errors"
max_iters: 4
---
# orders: consulta e troca de endereço (parte 1 da issue 14)

Testes: `-k "list or get_order or address or service_errors"` (não podem ser alterados). A nova
tentativa de pagamento é da parte 2 (`14b`): não crie `retry_payment` nem `POST /{id}/payment`.
Altere `orders/service.py` e `orders/router.py` com blocos EDIT; **não mexa em `checkout`**.

## service.py

Em todas: pedido inexistente → `NotFoundError`; de outro comprador → `ForbiddenError`. Use um
helper `_get_owned(session, order_id, buyer_id) -> Order` e devolva com `_order_to_view`.

- `get_order(session, order_id, buyer_id) -> OrderView`
- `list_by_buyer(session, buyer_id) -> list[OrderView]`: ordem `created_at` desc, depois `id` desc.
- `update_shipping_address(session, order_id, buyer_id, address: Address) -> OrderView`: campo
  vazio/só espaços → `InvalidInputError`; `status == CANCELLED` ou `fulfillment_status !=
  NOT_SHIPPED` → `ConflictError`. Grava os 5 campos `address_*` e faz `commit`.

## router.py

Mesmo padrão do `POST /checkout` (`service` importado como módulo, `Depends(get_session)`,
`Depends(get_current_user)`), todos com `response_model` de `OrderOut`:

- `GET ""` → `list[OrderOut]` do `auth.id`. Declare **antes** de `GET "/{order_id}"`.
- `GET "/{order_id}"` → `OrderOut`.
- `PATCH "/{order_id}/address"` com corpo `AddressIn` (já valida vazio → 422) → `OrderOut`.
