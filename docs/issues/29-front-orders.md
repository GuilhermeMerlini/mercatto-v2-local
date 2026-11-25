---
id: 29-front-orders
title: "front: meus pedidos e detalhes do pedido"
depends: [28-front-checkout]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/orders/AddressFields.tsx, backend/app/modules/orders/schemas.py, frontend/src/__tests__/issue_29_orders.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_29_orders.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: meus pedidos e detalhes do pedido

Os testes estão em `frontend/src/__tests__/issue_29_orders.test.tsx` e **não podem ser
alterados**.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

Crie `src/lib/orderStatus.ts`, que traduz os status:

| Campo | Valor | Texto |
|---|---|---|
| `status` | `PENDING`, `PROCESSING` | Processing |
| `status` | `PAID` | Paid |
| `status` | `FAILED` | Payment declined |
| `status` | `CANCELLED` | Cancelled |
| `fulfillment_status` | `NOT_SHIPPED` | Preparing shipment |
| `fulfillment_status` | `SHIPPED` | Shipped |
| `fulfillment_status` | `OUT_FOR_DELIVERY` | Out for delivery |
| `fulfillment_status` | `DELIVERED` | Delivered |

## Meus pedidos (`/orders`)

`GET /api/orders`. Um card por pedido, com:
- "Order #<id>";
- a data;
- o total;
- o status traduzido (se pago, o de entrega);
- "Estimated delivery: <date>", quando houver;
- um link "View details".

Sem pedidos → `EmptyState` com o título "You have no orders yet".

## Pedido (`/orders/:id`)

`GET /api/orders/:id`. 404 ou 403 → "Order not found".

- Com `?placed=1`: `PAID` mostra o banner "Order placed!"; `FAILED` mostra o alerta
  "Payment declined".
- Itens: busca nome e imagem em `GET /api/catalog/products/:id` de cada item. Se o produto não
  existir mais, mostra "Product unavailable".
- Mostra o total, o endereço, o método de entrega e a forma de pagamento.
- Linha do tempo da entrega com as 4 etapas. As concluídas mostram a data. Use uma lista
  ordenada e marque a etapa atual com `aria-current="step"`.
- Botão "Change address", só se `fulfillment_status === "NOT_SHIPPED"` e o pedido não está
  cancelado.
  - Abre `AddressFields` preenchido e "Save address" (`PATCH /api/orders/:id/address`).
  - 409 → `ErrorMessage`.
- Se `FAILED`: um rádio de forma de pagamento e o botão "Retry payment"
  (`POST /api/orders/:id/payment`).
  - A página se atualiza com o resultado.
  - 409 → `ErrorMessage` com o `detail`.
