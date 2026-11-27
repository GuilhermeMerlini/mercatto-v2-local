---
id: 26a-front-product
title: "front: página do produto (parte 1 da issue 26)"
depends: [24a-front-layout-home, 25b-front-account]
provides: [frontend/src/pages/Product.tsx, frontend/src/pages/Product.css]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/ui/Button.tsx, frontend/src/components/ui/Button.css, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/pages/Product.tsx, backend/app/modules/catalog/schemas.py, frontend/src/__tests__/issue_26a_product.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_26a_product.test.tsx src/__tests__/issue_24a_layout_home.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: página do produto (parte 1 da issue 26)

Os testes estão em `frontend/src/__tests__/issue_26a_product.test.tsx` e **não podem ser alterados**. Esta issue
troca o placeholder de `src/pages/Product.tsx`. Busque o produto com `api<Product>(...)` (de
`../api/client`; em erro ela lança `ApiError`, com `status` e `detail`) e use o tipo `Product` de
`../api/types` e os componentes de `components/ui`. As seções de produtos relacionados e de
avaliações **não** fazem parte desta issue (ficaram na 26b).

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

**Estrutura da página:** o `App.tsx` importa a página como **default**
(`import Product from "./pages/Product"`), então o arquivo termina em `export default`. O `Layout`
já renderiza o `<main>` em volta da página: a raiz da página é uma `<div>`, **nunca** outro `<main>`
(dois `<main>` quebram os testes). A rota `/products/:id` já existe no `App.tsx`: pegue o `id`
com `useParams()`.

**Estilos:** não há Tailwind nem nenhuma biblioteca de CSS no projeto. Cada componente ou página
tem o seu `.css`, importado no `.tsx`, com classes próprias que usam só `var(--token)` de
`tokens.css` (veja `Button.tsx` e `Button.css`). Um teste da 24a, que continua rodando, confere que **toda `className` usada em
`src/` existe em algum `.css`**.

**Como escrever os arquivos:** o `Product.tsx` atual é só um placeholder de 5 linhas: reescreva-o
**inteiro** com `### FILE`, e crie o `Product.css` também com `### FILE`. Nenhum outro arquivo
precisa mudar (não use `### EDIT` nesta issue). Um bloco `### FILE` nunca leva marcadores
`<<<<<<< SEARCH` / `>>>>>>> REPLACE`.

## API dos componentes de `components/ui` (importe de `../components/ui`)

- `Button`: props de `<button>` + `variant?: "primary" | "secondary" | "ghost"`, `loading?: boolean`.
- `Input` / `Select`: props de `<input>` / `<select>` + `label: string` (obrigatório), `error?: string`; o `Input` também aceita `hint?: string` (dica fixa abaixo do campo).
- `Card`: `as?: "div" | "article" | "section"`, `children`.
- `Price`: `cents: number`, `listCents?: number | null` (já formata o preço e mostra o preço antigo e o desconto).
- `StarRating`: `value: number`, `count?: number` (já renderiza a contagem entre parênteses).
- `Spinner`, `ErrorMessage({ children })`, `EmptyState({ title, children? })`.
- `Pagination`: `page`, `total`, `pageSize`, `onChange(page: number)`.

## Produto (`/products/:id`)

Carrega `GET /api/catalog/products/:id` ao abrir a página (e de novo se o `id` mudar). Enquanto
carrega, mostra o `Spinner`.

- 404 → `EmptyState` com o título "Product not found" (e nada do produto, sem `<h1>`).
- Outro erro → `ErrorMessage` com uma mensagem de erro (não é testado).

Com o produto carregado, mostra:

- a imagem (`<img>` com `src` = `image_url` e `alt` = nome do produto), se houver `image_url`;
- o nome num `<h1>`;
- a marca (`brand`), se houver, num elemento próprio cujo texto é **só** a marca (sem "Brand:");
- `StarRating` com `value={average_rating}` e `count={review_count}`, **só se**
  `review_count > 0`;
- `Price` com `cents={price_cents}` e `listCents={list_price_cents}`;
- a descrição, se houver;
- os detalhes, só os que existirem (por exemplo numa `<dl>`, cada rótulo e valor num elemento
  próprio):
  - rótulo "Model" com o `model_number`;
  - rótulo "Warranty" com `warranty_months` seguido de " months" (ex.: "12 months");
  - sem nenhum dos dois, nenhum rótulo aparece;
- a disponibilidade:
  - `stock > 0` → "In stock"; se além disso `stock < 10`, também "Only N left" (ex.: "Only 3 left")
    num elemento **separado** do "In stock";
  - `stock === 0` → "Out of stock" (e nada de "In stock");
- um contêiner vazio `<div data-slot="buy-box" />` (sem filhos nem texto), onde a issue 27 põe o
  botão de compra.
