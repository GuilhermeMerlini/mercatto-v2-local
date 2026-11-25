---
id: 24b-front-search
title: "front: página de busca (parte 2 da issue 24)"
depends: [24a-front-layout-home]
provides: [frontend/src/pages/Search.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/ProductCard.tsx, frontend/src/api/types.ts, frontend/src/pages/Home.tsx, backend/app/modules/search/schemas.py, frontend/src/__tests__/issue_24b_search.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_24a_layout_home.test.tsx src/__tests__/issue_24b_search.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: página de busca (parte 2 da issue 24)

Os testes estão em `frontend/src/__tests__/issue_24b_search.test.tsx` e **não podem ser alterados**. Os testes da 24a
também rodam e precisam continuar passando. Siga o `frontend/DESIGN.md`.

O layout, o `ProductCard` e a home já existem (issue 24a): use o `ProductCard` sem alterá-lo e
siga o padrão da `Home.tsx` (carregar com `api`, `Spinner` enquanto carrega, `ErrorMessage` no
erro). Esta issue troca o placeholder de `src/pages/Search.tsx`.

**Estilos:** não há Tailwind nem nenhuma biblioteca de CSS no projeto. Cada componente ou página
tem o seu `.css`, importado no `.tsx`, com classes próprias que usam só `var(--token)` de
`tokens.css` (veja `Button.tsx` e `Button.css`). Um teste confere que **toda `className` usada em
`src/` existe em algum `.css`**.

## API dos componentes de `components/ui` (importe de `../components/ui`)

- `Button`: props de `<button>` + `variant?: "primary" | "secondary" | "ghost"`, `loading?: boolean`.
- `Input` / `Select`: props de `<input>` / `<select>` + `label: string` (obrigatório), `error?: string`.
- `Card`: `as?: "div" | "article" | "section"`, `children`.
- `Price`: `cents: number`, `listCents?: number | null`.
- `StarRating`: `value: number`, `count?: number`.
- `Spinner`, `ErrorMessage({ children })`, `EmptyState({ title, children? })`.
- `Pagination`: `page`, `total`, `pageSize`, `onChange(page: number)`.

## Tipos da API

Acrescente em `src/api/types.ts`: `SearchResult = components["schemas"]["SearchOut"]` (o nome do
schema é exatamente este).

## Página de busca

- **Busca** (`/search`): o estado vem **da URL** (`useSearchParams`): `q`, `category`,
  `min_price` e `max_price` (em reais na URL, convertidos para centavos na API, nos parâmetros
  `min_price_cents` e `max_price_cents`, com `Math.round`), `min_rating`, `sort` e `page`.
  - Chama `GET /api/search/products` com esses parâmetros e `page_size=20`.
  - Título: `Resultados para "<q>"`, ou o nome da categoria, ou "Todos os produtos".
  - Se `corrected_query` vier preenchido, mostra o texto `Mostrando resultados para "<corrigido>"`
    (num só elemento, sem formatação dentro).
  - Mostra o total ("37 produtos").
  - Filtros:
    - um `Select` "Ordenar por", com as opções Relevância, Menor preço, Maior preço e Melhor
      avaliados (valores `relevance`, `price_asc`, `price_desc`, `rating`);
    - inputs "Preço mínimo" e "Preço máximo";
    - um `Select` "Avaliação mínima" (Qualquer, 4+, 3+, 2+; valores `""`, `4`, `3`, `2`).

    Mudar qualquer filtro atualiza a URL e volta para a página 1 (sem botão "Aplicar": os preços
    podem atualizar a cada mudança ou ao sair do campo).
  - Grade de `ProductCard`. Sem resultados: `EmptyState` com o título "Nenhum produto
    encontrado". Use o componente `Pagination`.
