---
id: 14b-orders-retry-payment
title: "orders: nova tentativa de pagamento (parte 2 da issue 14)"
depends: [13-orders-checkout, 14a-orders-read-address]
provides: [backend/app/modules/orders/service.py, backend/app/modules/orders/router.py]
context_files: [backend/app/modules/orders/models.py, backend/app/modules/orders/schemas.py, backend/app/modules/orders/service.py, backend/app/modules/orders/router.py, backend/tests/test_issue_14_orders_manage.py]
test_cmd: cd backend && python -m pytest tests/test_issue_14_orders_manage.py -q -k "retry"
max_iters: 4
---
# orders: nova tentativa de pagamento (parte 2 da issue 14)

Testes: `-k "retry"` (não podem ser alterados). Altere `orders/service.py`, `orders/schemas.py` e
`orders/router.py` com blocos EDIT; **não mexa em `checkout`** nem nas funções da parte 1.

## service.py

`retry_payment(session, order_id, buyer_id, payment_method) -> OrderView`:

1. `_get_owned` (inexistente → `NotFoundError`, de outro → `ForbiddenError`). Status diferente
   de `FAILED` → `ConflictError`.
2. Reivindica com `UPDATE` condicional e confere `rowcount` (0 → `ConflictError`):
   `session.execute(update(Order).where(Order.id == order_id, Order.status == OrderStatus.FAILED).values(status=OrderStatus.PROCESSING, payment_method=payment_method))`
   e `commit`. Não use `order.status = ...` nessa etapa.
3. Reserva de novo o estoque dos `OrderItem` do pedido com `catalog.decrease_stock`. Se falhar:
   devolve o que já reservou, volta o pedido para `FAILED` com `commit` e propaga o erro.
4. `payments.charge(order_id, total_cents, "BRL")`: aprovado → `PAID` com `paid_at` e
   `payment_transaction_id`; recusado → `FAILED` e devolve o estoque; exceção → `FAILED`,
   devolve o estoque e propaga. Faça `commit`, `session.refresh(order)` e devolva `_order_to_view`.

## schemas.py e router.py

`RetryPaymentIn`: `payment_method: PaymentMethod` (inválido → 422).
`POST "/{order_id}/payment"` com corpo `RetryPaymentIn` → `OrderOut`, mesmo padrão das outras rotas.
