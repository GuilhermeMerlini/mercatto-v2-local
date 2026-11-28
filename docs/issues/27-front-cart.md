---
id: 27-front-cart
title: "front: carrinho (contexto, contador no header e página)"
depends: [24a-front-layout-home, 25b-front-account, 26a-front-product]
provides: [frontend/src/cart/CartContext.tsx, frontend/src/pages/Cart.tsx, frontend/src/components/layout/Header.tsx, frontend/src/pages/Product.tsx, frontend/src/api/types.ts]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/auth/AuthContext.tsx, frontend/src/App.tsx, frontend/src/components/layout/Header.tsx, frontend/src/pages/Product.tsx, frontend/src/pages/Cart.tsx, backend/app/modules/cart/schemas.py, frontend/src/__tests__/issue_27_cart.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_27_cart.test.tsx src/__tests__/issue_26a_product.test.tsx src/__tests__/issue_24a_layout_home.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: carrinho (contexto, contador no header e página)

Os testes estão em `frontend/src/__tests__/issue_27_cart.test.tsx` e **não podem ser alterados**. Os testes da 26a
(página do produto) e da 24a (layout) também rodam e precisam continuar passando.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

**Estrutura das páginas:** o `App.tsx` importa cada página como **default**
(`import Cart from "./pages/Cart"`), então o arquivo termina em `export default`. O `Layout`
já renderiza o `<main>` em volta da página: a raiz da página é uma `<div>`, **nunca** outro `<main>`
(dois `<main>` quebram os testes).

**Estilos:** não há Tailwind nem nenhuma biblioteca de CSS no projeto. Cada componente ou página
tem o seu `.css`, importado no `.tsx`, com classes próprias que usam só `var(--token)` de
`tokens.css`. O CSS é global: não reaproveite um nome de classe que já existe em outro arquivo
(por exemplo `.product-card`, que é do `ProductCard`). Um teste da 24a, que continua rodando,
confere que **toda `className` usada em `src/` existe em algum `.css`**.

**Como escrever os arquivos:**
- com `### FILE` (arquivo inteiro): `src/cart/CartContext.tsx` (novo), `src/pages/Cart.tsx`
  (hoje é só um placeholder de 5 linhas) e `src/pages/Cart.css` (novo);
- com `### EDIT`: `src/App.tsx`, `src/components/layout/Header.tsx`, `src/pages/Product.tsx` e
  `src/api/types.ts` (e o `.css` deles, se acrescentar classes).

Um bloco `### FILE` nunca leva marcadores `<<<<<<< SEARCH` / `>>>>>>> REPLACE`.

## API dos componentes de `components/ui` (importe de `../components/ui`)

- `Button`: props de `<button>` + `variant?: "primary" | "secondary" | "ghost"`, `loading?: boolean`.
- `Input` / `Select`: props de `<input>` / `<select>` + `label: string` (obrigatório), `error?: string`; o `Input` também aceita `hint?: string` (dica fixa abaixo do campo). As opções do `Select` vão como `<option>` filhas (não há prop `options`).
- `Card`: `as?: "div" | "article" | "section"`, `children`.
- `Price`: `cents: number`, `listCents?: number | null`.
- `StarRating`: `value: number`, `count?: number`.
- `Spinner`, `ErrorMessage({ children })`, `EmptyState({ title, children? })`.
- `Pagination`: `page`, `total`, `pageSize`, `onChange(page: number)`.

## Tipos

Acrescente em `src/api/types.ts`: `export type Cart = components["schemas"]["CartView"];` (e, se
quiser, `CartItem` = `CartItemView`). No tipo gerado, **`items` e `saved_for_later` são
opcionais** (`items?: ...`): use `cart.items ?? []`, senão o `npm run build` quebra.

`CartView`: `{ user_id, items: CartItemView[], saved_for_later: CartItemView[], item_count,
total_cents }`. `CartItemView`: `{ product_id, product_name, image_url, unit_price_cents,
quantity, line_total_cents, saved_for_later }`. `item_count` é a soma das quantidades dos itens
do carrinho (os salvos para depois não contam).

## `src/cart/CartContext.tsx`

`CartProvider` e `useCart()`. O `CartProvider` fica **dentro** do `AuthProvider` em `App.tsx`
(envolvendo as `<Routes>`), porque usa o `user` de `useAuth()`. `useCart()` devolve:

```ts
{ cart: Cart | null, loading: boolean,
  addItem(productId, quantity), updateQuantity(productId, quantity), removeItem(productId),
  saveForLater(productId), moveToCart(productId), clear(), refresh() }   // todas Promise<void>
```

Rotas (todas com o `user.id` do usuário logado):

| Função | Rota |
|---|---|
| `refresh()` | `GET /api/cart/{user.id}` |
| `addItem(id, q)` | `POST /api/cart/{user.id}/items` com `{ product_id, quantity }` |
| `updateQuantity(id, q)` | `PUT /api/cart/{user.id}/items/{id}` com `{ quantity }` |
| `removeItem(id)` | `DELETE /api/cart/{user.id}/items/{id}` |
| `saveForLater(id)` | `POST /api/cart/{user.id}/items/{id}/save-for-later` |
| `moveToCart(id)` | `POST /api/cart/{user.id}/items/{id}/move-to-cart` |
| `clear()` | `DELETE /api/cart/{user.id}` |

- Todas as rotas devolvem o carrinho inteiro: cada operação substitui `cart` pela resposta.
- Deslogado: `cart` é `null` e as operações **não chamam a API** (só retornam).
- Recarrega quando o `user` muda: ao entrar, busca o carrinho; ao sair, `cart` volta a `null`.
- Erro ao carregar (ex.: 500) → `cart` fica `null`, sem lançar erro e **sem deslogar**.

## Header

Link "Cart" para `/cart`, sempre visível (logado ou não), com o número de itens
(`cart?.item_count ?? 0`) no texto. O nome acessível inclui o número:
`aria-label="Cart, 3 items"`, no singular com 1 (`"Cart, 1 item"`) e `"Cart, 0 items"` deslogado.
Não mude os outros links do header.

## Produto (buy-box)

Dentro do `<div data-slot="buy-box">` que já existe no `Product.tsx` (continua sendo um único
`<div>` com esse atributo):

- um `Select` com `label="Quantity"`, opções de 1 até `min(10, stock)`, começando em 1;
- o botão "Add to cart":
  - deslogado: navega para `/signin?next=/products/:id`, sem chamar a API;
  - esgotado (`stock === 0`): `disabled`;
  - logado: chama `addItem(product.id, quantidade)`.
- Depois de adicionar, mostra "Added to cart" num elemento com `role="status"`, com um link
  "View cart" para `/cart`.

Não repita na buy-box textos que a página já mostra ("In stock", "Out of stock"): os testes da
26a procuram cada um deles uma vez só.

## Carrinho (`/cart`)

A página tem um `<h1>` "Cart". Enquanto o carrinho carrega (ou `cart` é `null`), mostra o
`Spinner`.

- Itens (`cart.items`), num `<ul>`, **cada item num `<li>`** com:
  - a imagem (`<img alt={product_name}>`), se houver `image_url`, **fora** do link;
  - o nome como link para `/products/:product_id`;
  - o preço unitário (`unit_price_cents`, com `Price`);
  - um `Select` de quantidade com `label={"Quantity for " + product_name}`, opções de 1 a 10 (ou
    até a quantidade atual, se for maior), com a quantidade atual selecionada; mudar chama
    `updateQuantity`;
  - os botões "Save for later" e "Remove".
- Resumo: o texto "Subtotal (N items)" (com `item_count`; "Subtotal (1 item)" no singular), o
  total (`total_cents`, com `Price`) e o botão "Proceed to checkout", que navega para
  `/checkout` e fica `disabled` quando `cart.items` está vazio. O resumo aparece sempre, mesmo
  com o carrinho vazio.
- Seção "Saved for later", só se `cart.saved_for_later` tiver itens: um
  `<section aria-labelledby="...">` com um `<h2>` "Saved for later" e os itens num `<ul>`, cada um
  num `<li>` com imagem, nome como link, preço e os botões "Move to cart" e "Remove".
- `cart.items` vazio → no lugar da lista, `EmptyState` com o título "Your cart is empty" e, dentro
  dele, um link "Continue shopping" para `/`. A seção "Saved for later" continua aparecendo se
  houver itens salvos.
