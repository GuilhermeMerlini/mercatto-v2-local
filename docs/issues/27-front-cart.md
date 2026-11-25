---
id: 27-front-cart
title: "front: carrinho (contexto, contador no header e página)"
depends: [26-front-product]
provides: [frontend/src/cart/CartContext.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/App.tsx, frontend/src/components/layout/Header.tsx, frontend/src/pages/Product.tsx, backend/app/modules/cart/schemas.py, frontend/src/__tests__/issue_27_cart.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_27_cart.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: carrinho (contexto, contador no header e página)

Os testes estão em `frontend/src/__tests__/issue_27_cart.test.tsx` e **não podem ser alterados**.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## `src/cart/CartContext.tsx`

`CartProvider` (dentro de `AuthProvider` em `App.tsx`) e `useCart()`, que devolve
`{ cart: Cart | null, loading, addItem(productId, quantity), updateQuantity(productId, q),
removeItem(productId), saveForLater(productId), moveToCart(productId), clear(), refresh() }`.

- Usa as rotas `/api/cart/{user.id}/...`. Cada operação substitui `cart` pela resposta da API.
- Deslogado: `cart` é `null` e as operações não chamam a API.
- Recarrega quando o usuário muda.

## Header

Link "Cart" para `/cart`, com o número de itens (`item_count`). O nome acessível inclui o
número: `aria-label="Cart, 3 items"`.

## Produto

No `data-slot="buy-box"`:
- um `Select` "Quantity" (1 até `min(10, stock)`);
- o botão "Add to cart". Deslogado, ele leva para `/signin?next=/products/:id`.
  Esgotado, fica desabilitado.

Depois de adicionar, mostra "Added to cart" (`role="status"`) com um link "View
cart".

## Carrinho (`/cart`)

- Itens: imagem, nome (link), preço unitário, um `Select` de quantidade com rótulo
  "Quantity for <name>" e os botões "Save for later" e "Remove".
- Resumo: "Subtotal (N items)" com `total_cents` e o botão "Proceed to checkout", que leva para
  `/checkout` e fica desabilitado com o carrinho vazio.
- Seção "Saved for later", só se houver itens, com os botões "Move to cart" e
  "Remove".
- Carrinho vazio → `EmptyState` com o título "Your cart is empty" e um link "Continue shopping".
