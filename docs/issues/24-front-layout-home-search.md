---
id: 24-front-layout-home-search
title: "front: layout, home e busca"
depends: [22-front-scaffold, 23-front-design]
provides: [frontend/src/components/layout/Layout.tsx, frontend/src/components/ProductCard.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/App.tsx, backend/app/modules/search/schemas.py, backend/app/modules/catalog/schemas.py, frontend/src/__tests__/issue_24_layout_home_search.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_24_layout_home_search.test.tsx
max_iters: 5
---
# front: layout, home e busca

Os testes estão em `frontend/src/__tests__/issue_24_layout_home_search.test.tsx` e **não podem
ser alterados**. Siga o `frontend/DESIGN.md` e use os componentes de `components/ui`.

## `components/layout/`

- `Header`
  - Logo "Mercatto" como link para `/`.
  - Formulário de busca com `role="search"`, input com rótulo acessível "Buscar produtos" e
    botão "Buscar". Ao enviar, navega para `/search?q=<texto>`.
  - Deslogado: link "Entrar" para `/signin`.
  - Logado: o nome do usuário, um link "Meus pedidos" para `/orders`, um link "Minha conta"
    para `/account` e o botão "Sair".
  - Se for `SELLER`, também um link "Painel do vendedor" para `/seller`.
- `Footer`
- `Layout`: Header + `<main>` + Footer. Envolve todas as rotas em `App.tsx` (use `<Outlet/>`).

## `components/ProductCard.tsx`

`<article>` com:
- imagem (`alt` = nome do produto, `loading="lazy"`; sem `image_url`, um placeholder);
- o nome como link para `/products/:id`;
- `Price`;
- `StarRating`, só se `review_count > 0`;
- o texto "Esgotado" quando `stock === 0`.

## Páginas

- **Home** (`/`)
  - Carrega `GET /api/catalog/categories` e mostra cada categoria como link para
    `/search?category=<nome>`.
  - Carrega `GET /api/catalog/products?page_size=12` e mostra uma grade de `ProductCard`.
  - Enquanto carrega: `Spinner`. Erro: `ErrorMessage`.
- **Busca** (`/search`): o estado vem **da URL** (`useSearchParams`): `q`, `category`,
  `min_price` e `max_price` (em reais na URL, convertidos para centavos na API), `min_rating`,
  `sort` e `page`.
  - Chama `GET /api/search/products` com esses parâmetros e `page_size=20`.
  - Título: `Resultados para "<q>"`, ou o nome da categoria, ou "Todos os produtos".
  - Se `corrected_query` vier preenchido, mostra `Mostrando resultados para "<corrigido>"`.
  - Mostra o total ("37 produtos").
  - Filtros:
    - um `Select` "Ordenar por", com as opções Relevância, Menor preço, Maior preço e Melhor
      avaliados (valores `relevance`, `price_asc`, `price_desc`, `rating`);
    - inputs "Preço mínimo" e "Preço máximo";
    - um `Select` "Avaliação mínima" (Qualquer, 4+, 3+, 2+).

    Mudar qualquer filtro atualiza a URL e volta para a página 1.
  - Grade de `ProductCard`. Sem resultados: `EmptyState` com o título "Nenhum produto
    encontrado". Use o componente `Pagination`.
