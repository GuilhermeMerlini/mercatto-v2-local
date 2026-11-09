---
id: 12-payments-mock
title: "payments: gateway mock"
depends: []
provides: [backend/app/modules/payments/service.py, backend/app/modules/payments/gateway.py]
context_files: [backend/app/core/config.py, backend/app/core/errors.py, backend/tests/test_issue_12_payments_mock.py]
test_cmd: cd backend && python -m pytest tests/test_issue_12_payments_mock.py -q
max_iters: 4
---
# payments: gateway mock

Os testes estão em `backend/tests/test_issue_12_payments_mock.py` e **não podem ser alterados**.
Este módulo não depende de nenhum outro e não tem tabelas nem endpoints.

## Criar `backend/app/modules/payments/gateway.py`

- `PaymentResult`: `@dataclass(frozen=True)` com `approved: bool`, `transaction_id: str | None`
  e `message: str`.
- `PaymentGateway(Protocol)` com `charge(self, order_id: int, amount_cents: int, currency: str)
  -> PaymentResult`.
- `MockPaymentGateway(decline_mode="none")`
  - `"none"`: aprova tudo, com `transaction_id` único começando com `"mock_"`.
  - `"always"`: recusa tudo (`approved=False`, `transaction_id=None`).
  - `"first-attempt"`: recusa a **primeira** cobrança de cada `order_id` e aprova as seguintes.
    Precisa ser thread-safe.
  - Outro valor → `ValueError` no construtor.

## Criar `backend/app/modules/payments/service.py`

- `charge(order_id, amount_cents, currency="BRL") -> PaymentResult`: `amount_cents <= 0` →
  `InvalidInputError`. Delega ao gateway atual.
- `set_gateway(gateway) -> None`: troca o gateway (usado nos testes).
- O gateway inicial é `MockPaymentGateway(config.PAYMENT_MOCK_DECLINE)`.
- Reexporte `PaymentResult`, `PaymentGateway` e `MockPaymentGateway`, para outros módulos só
  importarem `payments.service`.
