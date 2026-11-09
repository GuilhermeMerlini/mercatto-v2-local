---
id: 29-front-orders
title: "front: meus pedidos e detalhes do pedido"
depends: [28-front-checkout]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/orders/AddressFields.tsx, backend/app/modules/orders/schemas.py, frontend/src/__tests__/issue_29_orders.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_29_orders.test.tsx
max_iters: 5
---
# front: meus pedidos e detalhes do pedido

Os testes estão em `frontend/src/__tests__/issue_29_orders.test.tsx` e **não podem ser
alterados**.

Crie `src/lib/orderStatus.ts`, que traduz os status:

| Campo | Valor | Texto |
|---|---|---|
| `status` | `PENDING`, `PROCESSING` | Processando |
| `status` | `PAID` | Pago |
| `status` | `FAILED` | Pagamento recusado |
| `status` | `CANCELLED` | Cancelado |
| `fulfillment_status` | `NOT_SHIPPED` | Preparando envio |
| `fulfillment_status` | `SHIPPED` | Enviado |
| `fulfillment_status` | `OUT_FOR_DELIVERY` | Saiu para entrega |
| `fulfillment_status` | `DELIVERED` | Entregue |

## Meus pedidos (`/orders`)

`GET /api/orders`. Um card por pedido, com:
- "Pedido #<id>";
- a data;
- o total;
- o status traduzido (se pago, o de entrega);
- "Entrega prevista: <data>", quando houver;
- um link "Ver detalhes".

Sem pedidos → `EmptyState` com o título "Você ainda não fez pedidos".

## Pedido (`/orders/:id`)

`GET /api/orders/:id`. 404 ou 403 → "Pedido não encontrado".

- Com `?placed=1`: `PAID` mostra o banner "Pedido confirmado!"; `FAILED` mostra o alerta
  "Pagamento recusado".
- Itens: busca nome e imagem em `GET /api/catalog/products/:id` de cada item. Se o produto não
  existir mais, mostra "Produto indisponível".
- Mostra o total, o endereço, o método de entrega e a forma de pagamento.
- Linha do tempo da entrega com as 4 etapas. As concluídas mostram a data. Use uma lista
  ordenada e marque a etapa atual com `aria-current="step"`.
- Botão "Alterar endereço", só se `fulfillment_status === "NOT_SHIPPED"` e o pedido não está
  cancelado.
  - Abre `AddressFields` preenchido e "Salvar endereço" (`PATCH /api/orders/:id/address`).
  - 409 → `ErrorMessage`.
- Se `FAILED`: um rádio de forma de pagamento e o botão "Tentar pagar novamente"
  (`POST /api/orders/:id/payment`).
  - A página se atualiza com o resultado.
  - 409 → `ErrorMessage` com o `detail`.
