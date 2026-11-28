---
id: 28-front-checkout
title: "front: checkout e confirmação do pedido"
depends: [27-front-cart]
provides: [frontend/src/components/orders/AddressFields.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, backend/app/modules/orders/schemas.py, frontend/src/__tests__/issue_28_checkout.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_28_checkout.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: checkout e confirmação do pedido

Os testes estão em `frontend/src/__tests__/issue_28_checkout.test.tsx` e **não podem ser
alterados**.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## `components/orders/AddressFields.tsx`

Os campos "Full name", "Address", "City", "State" e "ZIP code", controlados
(`value`/`onChange`), cada um com o seu erro. Será reutilizado na issue 29.

## Finalizar compra (`/checkout`)

Só itens do carrinho fora de "Save for later". Carrinho vazio → redireciona para `/cart`.

1. **Endereço**: `AddressFields`. Todos obrigatórios: o erro é "Required field" no próprio
   campo, sem chamar a API.
2. **Entrega**: rádio "Standard (5 business days)", "Express (1 business day)" e "Store pickup"
   (`STANDARD`, `EXPRESS`, `PICKUP`).
3. **Pagamento**: rádio "Card", "Store credit" e "Gift card" (`CARD`, `STORE`, `GIFT`).
4. **Resumo**: itens, quantidades e total, e o botão "Place order".

Ao confirmar:
- Chama `POST /api/orders/checkout` com o header `Idempotency-Key`. A chave é um
  `crypto.randomUUID()` gerado **uma vez** por visita à página, para que um clique duplo não
  crie dois pedidos.
- O botão fica com `loading`.
- Pedido `PAID` → remove do carrinho os itens comprados (`removeItem` em cada um) e navega para
  `/orders/:id?placed=1`.
- Pedido `FAILED` → navega para `/orders/:id?placed=1` também, onde a issue 29 oferece a nova
  tentativa.
- 409 (estoque) → `ErrorMessage` com o `detail` da API, e continua na página.
