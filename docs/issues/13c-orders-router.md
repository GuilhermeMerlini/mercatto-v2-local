---
id: 13c-orders-router
title: "orders: rota de checkout (parte 3 da issue 13)"
depends: [13a-orders-models-delivery, 13b-orders-service]
provides: [backend/app/modules/orders/schemas.py, backend/app/modules/orders/router.py]
context_files: [backend/app/main.py, backend/app/core/deps.py, backend/app/modules/orders/service.py, backend/tests/conftest.py, backend/tests/test_issue_13_orders_checkout.py]
test_cmd: cd backend && python -m pytest tests/test_issue_13_orders_checkout.py -q -k "not tables and not delivery and not service_ and not gateway_exception and not before_charge"
max_iters: 4
---
# orders: rota de checkout (parte 3 da issue 13)

Testes: os HTTP (não podem ser alterados). Altere `orders/schemas.py`, `orders/router.py` e
`main.py`. `service.py` já está pronto: só mexa nele com EDIT pontual se um teste falhar por
regra de negócio, sem mudar assinaturas.

## schemas.py

`CheckoutIn`: `items: list[CheckoutItemIn] = Field(min_length=1)` (`product_id`,
`quantity: int = Field(ge=1)`), `address: AddressIn` (5 campos `str`, com `field_validator` que
rejeita vazio/só espaços), `shipping_method` e `payment_method` (enums de `models.py`).
`OrderOut` com os mesmos campos de `OrderView` e `address` aninhado. Erros de validação viram 422
sozinhos.

## router.py

`APIRouter(prefix="/api/orders")`, registrado em `main.py`. `POST /checkout` → 200 com `OrderOut`:

```python
def checkout(data: CheckoutIn,
             idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
             auth: AuthUser = Depends(get_current_user),
             session: Session = Depends(get_session)):  # get_session de app.core.db
```

`auth.require_role("BUYER")`, converte para `CheckoutItem`/`Address` e chama `service.checkout`.
Sem `try/except` nem `HTTPException`: 404/409 vêm do handler de `main.py`.
