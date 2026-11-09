---
id: 26-front-product
title: "front: página do produto, relacionados e avaliações"
depends: [24-front-layout-home-search, 25-front-auth-account]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, backend/app/modules/catalog/schemas.py, backend/app/modules/reviews/schemas.py, frontend/src/__tests__/issue_26_product.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_26_product.test.tsx
max_iters: 5
---
# front: página do produto, relacionados e avaliações

Os testes estão em `frontend/src/__tests__/issue_26_product.test.tsx` e **não podem ser
alterados**.

## Produto (`/products/:id`)

Carrega `GET /api/catalog/products/:id`. 404 → `EmptyState` com o título "Produto não
encontrado". Mostra:

- imagem grande, nome em `<h1>`, marca, `StarRating` com a contagem, `Price` e descrição;
- detalhes (modelo, garantia em meses), só os que existirem;
- disponibilidade: "Em estoque" (com "Restam N" se `stock < 10`) ou "Esgotado";
- um contêiner vazio `<div data-slot="buy-box" />` onde a issue 27 põe o botão de compra.

## Relacionados

`GET /api/catalog/products/:id/related?limit=6`. Seção "Produtos relacionados" com `ProductCard`.
Abaixo de cada card vai o motivo principal (`primary_reason`), traduzido:

| `primary_reason` | Texto |
|---|---|
| `TOP_RATED_IN_CATEGORY` | Mais bem avaliado da categoria |
| `LOWER_PRICE` | Mais barato |
| `SAME_BRAND` | Mesma marca |
| `SIMILAR_NAME` | Parecido |
| `HIGHER_RATED` | Mais bem avaliado |
| `SAME_CATEGORY` | Mesma categoria |

Lista vazia → a seção não aparece.

## Avaliações

`GET /api/reviews/products/:id`. Seção "Avaliações".

- Resumo: média e total.
- Lista: autor, `StarRating`, título, texto e data (`toLocaleDateString("pt-BR")`).
- Cada avaliação tem o botão "Útil (N)", que chama `POST /api/reviews/:id/helpful` e atualiza o
  número.
- Sem avaliações → "Este produto ainda não tem avaliações".
- Logado: formulário "Escrever avaliação".
  - Nota de 1 a 5 em grupo de rádio com rótulos "1 estrela" … "5 estrelas".
  - Campos "Título" e "Comentário" (opcional) e botão "Publicar avaliação".
  - Ao publicar, a avaliação aparece no topo da lista e a nota média é recarregada.
  - Sem nota → erro "Escolha uma nota".
- Deslogado: link "Entre para avaliar" para `/signin?next=/products/:id`.
