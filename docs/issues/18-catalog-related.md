---
id: 18-catalog-related
title: "catalog: produtos relacionados"
depends: [06-catalog-read]
provides: [backend/app/modules/catalog/service.py, backend/app/modules/catalog/related.py]
context_files: [backend/app/modules/catalog/models.py, backend/app/modules/catalog/schemas.py, backend/app/modules/catalog/router.py, backend/tests/conftest.py, backend/tests/test_issue_18_catalog_related.py]
test_cmd: cd backend && python -m pytest tests/test_issue_18_catalog_related.py tests/test_issue_06_catalog_read.py -q
max_iters: 5
---
# catalog: produtos relacionados

Os testes estão em `backend/tests/test_issue_18_catalog_related.py` e **não podem ser alterados**.

## Criar `backend/app/modules/catalog/related.py` (puro: sem banco, sem FastAPI)

Os produtos são objetos com os atributos de `ProductView`. Para tipá-los sem import circular, use
`from __future__ import annotations` e `if TYPE_CHECKING: from app.modules.catalog.service import
ProductView`.

- `RelatedReason(str, Enum)`, em ordem de prioridade: `TOP_RATED_IN_CATEGORY`, `LOWER_PRICE`,
  `SAME_BRAND`, `SIMILAR_NAME`, `HIGHER_RATED`, `SAME_CATEGORY`.
- `name_tokens(name) -> set[str]`: minúsculas, divididas em não-alfanuméricos.
  - Mantém tokens com 3+ caracteres.
  - Descarta números puros e as stop words: `the and for with from into your you our this that
    are all pack packs set sets new inch inches piece pieces pcs count size men mens women
    womens kids kid boys girls baby unisex adult adults`.
- `longest_name_tokens(name, limit) -> list[str]`: os tokens mais longos (empate: ordem
  alfabética).
- `is_real_brand(brand) -> bool`: falso se:
  - for vazio ou tiver dígito;
  - for stop word;
  - estiver em `women's womens men's mens kids kids' kid's boys boys' boy's girls girls'
    girl's children's baby toddler unisex adult the a an new pack set wireless portable premium
    large small mini stainless adjustable universal professional original` (comparação em
    minúsculas, com `’` trocado por `'`).
- `same_brand(a, b)`: as duas são marcas reais e iguais, ignorando maiúsculas e espaços nas
  pontas.
- `score(current, candidate, category_top_rating: float | None) -> Scored`. `Scored` é uma
  dataclass com `product`, `score` e `reasons`.

  Pontos:
  - mesma categoria: +3.0;
  - mesma marca: +2.0;
  - nome: +2.0 × Jaccard dos `name_tokens`;
  - preço: +1.5 × `max(0, 1 − |p_cand − p_atual| / p_atual)` (0 se `p_atual <= 0`);
  - nota: +1.0 × `nota_cand / 5`, só se o candidato tem avaliações.

  Motivos (`reasons`, sempre na ordem do enum):
  - `TOP_RATED_IN_CATEGORY`: mesma categoria, candidato com avaliações e nota
    `>= category_top_rating` (não nulo);
  - `LOWER_PRICE`: mesma categoria e mais barato;
  - `SAME_BRAND`;
  - `SIMILAR_NAME`: 2+ tokens em comum;
  - `HIGHER_RATED`: candidato com avaliações e nota maior que a do atual;
  - `SAME_CATEGORY`.
- `sort_key(scored)`: score desc, `review_count` desc, `id` asc.

## Nova função em `catalog/service.py`

- `RelatedProduct`: dataclass congelada com `product: ProductView`, `score` (arredondado a 3
  casas), `primary_reason` (o primeiro motivo, ou `None`) e `reasons`.
  Reexporte `RelatedReason`.
- `find_related(session, product_id, limit=6) -> list[RelatedProduct]`. Produto inexistente →
  `NotFoundError`.
  1. Candidatos: até 200 produtos da **mesma categoria**, em estoque (`stock > 0`), exceto o
     próprio.
  2. Só se forem menos que `limit`, entram candidatos de **outras** categorias, em estoque. São
     até 50 com a mesma marca real e até 50 cujo nome contém um dos 3 `longest_name_tokens`.
     Desses, ficam apenas os que têm `SAME_BRAND` ou `SIMILAR_NAME`. Nunca complete a lista
     com produtos sem relação.
  3. `category_top_rating`: maior `average_rating` entre os produtos avaliados da categoria.
  4. Ordena por `sort_key` e corta em `limit`.

## Novo endpoint (público)

`GET /api/catalog/products/{id}/related?limit=6` → **200**
`[{product, score, primary_reason, reasons}]`. `limit` vai de 1 a 20 (senão **422**). Produto
inexistente → **404**.
