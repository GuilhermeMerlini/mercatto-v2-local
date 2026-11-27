---
id: 26-front-product
title: "front: página do produto, relacionados e avaliações"
depends: [24-front-layout-home-search, 25-front-auth-account]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, backend/app/modules/catalog/schemas.py, backend/app/modules/reviews/schemas.py, frontend/src/__tests__/issue_26a_product.test.tsx, frontend/src/__tests__/issue_26b_related_reviews.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_26a_product.test.tsx src/__tests__/issue_26b_related_reviews.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: página do produto, relacionados e avaliações

Dividida em **26a** (página do produto, issue #26 no GitHub) e **26b** (relacionados e
avaliações, issue #58 no GitHub, que depende do backend das issues 15, 16 e 18). Os testes estão em
`frontend/src/__tests__/issue_26a_product.test.tsx` e `issue_26b_related_reviews.test.tsx` e
**não podem ser alterados**.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## Produto (`/products/:id`) — 26a

Carrega `GET /api/catalog/products/:id`. 404 → `EmptyState` com o título "Product not
found". Mostra:

- imagem grande, nome em `<h1>`, marca, `Price` e descrição;
- `StarRating` com a contagem (`average_rating` e `review_count` do próprio produto), só se
  `review_count > 0`;
- detalhes (modelo, garantia em meses), só os que existirem;
- disponibilidade: "In stock" (com "Only N left" se `stock < 10`) ou "Out of stock";
- um contêiner vazio `<div data-slot="buy-box" />` onde a issue 27 põe o botão de compra.

## Relacionados — 26b

`GET /api/catalog/products/:id/related?limit=6`. Seção "Related products" com `ProductCard` e,
abaixo de cada card, o motivo principal (`primary_reason`) traduzido. Lista vazia → a seção não
aparece. A tabela dos motivos está em `26b-front-related-reviews.md`.

## Avaliações — 26b

`GET /api/reviews/products/:id`. Seção "Reviews" com resumo, lista, botão "Helpful (N)",
"No reviews yet" quando vazia, formulário "Write a review" para quem está logado e link
"Sign in to write a review" para quem não está. Detalhes em `26b-front-related-reviews.md`.
