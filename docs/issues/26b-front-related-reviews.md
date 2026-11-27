---
id: 26b-front-related-reviews
title: "front: produtos relacionados e avaliações (parte 2 da issue 26)"
depends: [26a-front-product, 15-reviews-create-list, 16-reviews-helpful, 18-catalog-related]
provides: [frontend/src/pages/Product.tsx, frontend/src/pages/Product.css]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/pages/Product.tsx, frontend/src/pages/Product.css, frontend/src/components/ProductCard.tsx, frontend/src/api/client.ts, frontend/src/api/types.ts, backend/app/modules/catalog/schemas.py, backend/app/modules/reviews/schemas.py, frontend/src/__tests__/issue_26b_related_reviews.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_26a_product.test.tsx src/__tests__/issue_26b_related_reviews.test.tsx src/__tests__/issue_24a_layout_home.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: produtos relacionados e avaliações (parte 2 da issue 26)

Corresponde à issue #58 no GitHub. Fica para depois do backend de avaliações (15, 16) e de
relacionados (18), que ainda não têm rotas.

Os testes estão em `frontend/src/__tests__/issue_26b_related_reviews.test.tsx` e **não podem
ser alterados**. Os testes da 26a também rodam e precisam continuar passando. Esta issue
acrescenta as duas seções à página `src/pages/Product.tsx` feita na 26a.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## Relacionados

`GET /api/catalog/products/:id/related?limit=6`. Seção "Related products" com `ProductCard`.
Abaixo de cada card vai o motivo principal (`primary_reason`), traduzido:

| `primary_reason` | Texto |
|---|---|
| `TOP_RATED_IN_CATEGORY` | Top rated in category |
| `LOWER_PRICE` | Lower price |
| `SAME_BRAND` | Same brand |
| `SIMILAR_NAME` | Similar |
| `HIGHER_RATED` | Higher rated |
| `SAME_CATEGORY` | Same category |

Lista vazia → a seção não aparece.

## Avaliações

`GET /api/reviews/products/:id`. Seção "Reviews".

- Resumo: média e total.
- Lista: autor, `StarRating`, título, texto e data (`toLocaleDateString("en-US")`).
- Cada avaliação tem o botão "Helpful (N)", que chama `POST /api/reviews/:id/helpful` e atualiza o
  número.
- Sem avaliações → "No reviews yet".
- Logado: formulário "Write a review".
  - Nota de 1 a 5 em grupo de rádio com rótulos "1 star" … "5 stars".
  - Campos "Title" e "Comment" (opcional) e botão "Submit review".
  - Ao publicar, a avaliação aparece no topo da lista e a nota média é recarregada.
  - Sem nota → erro "Choose a rating".
- Deslogado: link "Sign in to write a review" para `/signin?next=/products/:id`.
