---
id: 30-front-seller
title: "front: painel do vendedor"
depends: [29-front-orders]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/lib/orderStatus.ts, backend/app/modules/sellers/schemas.py, backend/app/modules/catalog/schemas.py, frontend/src/__tests__/issue_30_seller.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_30_seller.test.tsx
max_iters: 5
---
# front: painel do vendedor

Os testes estão em `frontend/src/__tests__/issue_30_seller.test.tsx` e **não podem ser
alterados**. Rota `/seller`, só `SELLER`. Três abas acessíveis (`role="tablist"`, `role="tab"` e
`role="tabpanel"`): "Visão geral", "Produtos" e "Pedidos". A aba ativa fica na URL
(`?tab=overview|products|orders`).

## Visão geral

`GET /api/sellers/{id}/metrics`. Mostra:
- "Receita" (`total_revenue_cents`, formatado);
- "Pedidos recebidos" (a quantidade, de `GET /api/sellers/{id}/orders`);
- a lista "Estoque baixo", com nome e estoque, ou "Nenhum produto com estoque baixo".

## Produtos

`GET /api/sellers/{id}/products` com `Pagination`.
- Tabela com as colunas Produto, Preço, Estoque e Nota, e as ações "Editar" e "Excluir" em cada
  linha.
- Botão "Novo produto".
- Formulário (criar e editar):
  - campos: Nome, Descrição, Preço (em reais; envia `price_cents`), "Preço original"
    (opcional; `list_price_cents`), Estoque, Categoria, "URL da imagem", Marca, Modelo,
    "Garantia (meses)";
  - salva com `POST` ou `PUT /api/catalog/products[/:id]`;
  - erros 400/422 aparecem em `ErrorMessage` com o `detail`.
- "Excluir" pede confirmação ("Excluir <nome>?") com os botões "Excluir" e "Cancelar".
  Confirmado, chama `DELETE` e remove a linha.

## Pedidos

`GET /api/sellers/{id}/orders`. Uma linha por pedido, com o número, a data, os itens do vendedor,
o subtotal e o status de entrega traduzido (`lib/orderStatus.ts`).

Para pedido `PAID` ainda não entregue, mostre um botão com a próxima etapa:

| Etapa atual | Botão | Envia |
|---|---|---|
| `NOT_SHIPPED` | Marcar como enviado | `SHIPPED` |
| `SHIPPED` | Saiu para entrega | `OUT_FOR_DELIVERY` |
| `OUT_FOR_DELIVERY` | Marcar como entregue | `DELIVERED` |

O botão chama `POST /api/sellers/{id}/orders/{order_id}/fulfillment` e atualiza a linha.
