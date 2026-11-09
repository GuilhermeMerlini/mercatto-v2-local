---
id: 27-front-cart
title: "front: carrinho (contexto, contador no header e página)"
depends: [26-front-product]
provides: [frontend/src/cart/CartContext.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/App.tsx, frontend/src/components/layout/Header.tsx, frontend/src/pages/Product.tsx, backend/app/modules/cart/schemas.py, frontend/src/__tests__/issue_27_cart.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_27_cart.test.tsx
max_iters: 5
---
# front: carrinho (contexto, contador no header e página)

Os testes estão em `frontend/src/__tests__/issue_27_cart.test.tsx` e **não podem ser alterados**.

## `src/cart/CartContext.tsx`

`CartProvider` (dentro de `AuthProvider` em `App.tsx`) e `useCart()`, que devolve
`{ cart: Cart | null, loading, addItem(productId, quantity), updateQuantity(productId, q),
removeItem(productId), saveForLater(productId), moveToCart(productId), clear(), refresh() }`.

- Usa as rotas `/api/cart/{user.id}/...`. Cada operação substitui `cart` pela resposta da API.
- Deslogado: `cart` é `null` e as operações não chamam a API.
- Recarrega quando o usuário muda.

## Header

Link "Carrinho" para `/cart`, com o número de itens (`item_count`). O nome acessível inclui o
número: `aria-label="Carrinho, 3 itens"`.

## Produto

No `data-slot="buy-box"`:
- um `Select` "Quantidade" (1 até `min(10, stock)`);
- o botão "Adicionar ao carrinho". Deslogado, ele leva para `/signin?next=/products/:id`.
  Esgotado, fica desabilitado.

Depois de adicionar, mostra "Adicionado ao carrinho" (`role="status"`) com um link "Ver
carrinho".

## Carrinho (`/cart`)

- Itens: imagem, nome (link), preço unitário, um `Select` de quantidade com rótulo
  "Quantidade de <nome>" e os botões "Salvar para depois" e "Remover".
- Resumo: "Subtotal (N itens)" com `total_cents` e o botão "Finalizar compra", que leva para
  `/checkout` e fica desabilitado com o carrinho vazio.
- Seção "Salvos para depois", só se houver itens, com os botões "Mover para o carrinho" e
  "Remover".
- Carrinho vazio → `EmptyState` com o título "Seu carrinho está vazio" e um link para continuar
  comprando.
