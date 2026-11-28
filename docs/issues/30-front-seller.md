---
id: 30-front-seller
title: "front: painel do vendedor"
depends: [29-front-orders]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/lib/orderStatus.ts, backend/app/modules/sellers/schemas.py, backend/app/modules/catalog/schemas.py, frontend/src/__tests__/issue_30_seller.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_30_seller.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: painel do vendedor

Os testes estão em `frontend/src/__tests__/issue_30_seller.test.tsx` e **não podem ser
alterados**. Rota `/seller`, só `SELLER`. Três abas acessíveis (`role="tablist"`, `role="tab"` e
`role="tabpanel"`): "Overview", "Products" e "Orders". A aba ativa fica na URL
(`?tab=overview|products|orders`).

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## Visão geral

`GET /api/sellers/{id}/metrics`. Mostra:
- "Revenue" (`total_revenue_cents`, formatado);
- "Orders received" (a quantidade, de `GET /api/sellers/{id}/orders`);
- a lista "Low stock", com nome e estoque, ou "No products with low stock".

## Produtos

`GET /api/sellers/{id}/products` com `Pagination`.
- Tabela com as colunas Product, Price, Stock e Rating, e as ações "Edit" e "Delete" em cada
  linha.
- Botão "New product".
- Formulário (criar e editar):
  - campos: Name, Description, Price (em dólares; envia `price_cents`), "List price"
    (opcional; `list_price_cents`), Stock, Category, "Image URL", Brand, Model,
    "Warranty (months)";
  - salva com `POST` ou `PUT /api/catalog/products[/:id]`;
  - erros 400/422 aparecem em `ErrorMessage` com o `detail`.
- "Delete" pede confirmação ("Delete <name>?") com os botões "Delete" e "Cancel".
  Confirmado, chama `DELETE` e remove a linha.

## Pedidos

`GET /api/sellers/{id}/orders`. Uma linha por pedido, com o número, a data, os itens do vendedor,
o subtotal e o status de entrega traduzido (`lib/orderStatus.ts`).

Para pedido `PAID` ainda não entregue, mostre um botão com a próxima etapa:

| Etapa atual | Botão | Envia |
|---|---|---|
| `NOT_SHIPPED` | Mark as shipped | `SHIPPED` |
| `SHIPPED` | Mark as out for delivery | `OUT_FOR_DELIVERY` |
| `OUT_FOR_DELIVERY` | Mark as delivered | `DELIVERED` |

O botão chama `POST /api/sellers/{id}/orders/{order_id}/fulfillment` e atualiza a linha.
