---
id: 09-search-service
title: "search: busca com filtros, ordenação e correção de typo"
depends: [06-catalog-read, 08-search-ranker]
provides: [backend/app/modules/search/service.py]
context_files: [backend/app/main.py, backend/app/core/errors.py, backend/app/modules/catalog/schemas.py, backend/tests/conftest.py, backend/tests/test_issue_09_search_service.py]
test_cmd: cd backend && python -m pytest tests/test_issue_09_search_service.py -q
max_iters: 4
---
# search: busca com filtros, ordenação e correção de typo

Os testes estão em `backend/tests/test_issue_09_search_service.py` e **não podem ser alterados**.

## Criar `backend/app/modules/search/{service,schemas,router}.py`

**service.py**: usa `catalog.service.filter_products` para os candidatos e `ranker` para o
texto.

- `SearchResult`: `@dataclass(frozen=True)` com `items: list[ProductView]`, `total`, `page`,
  `page_size` e `corrected_query: str | None`.
- `search_products(session, query=None, category=None, min_price_cents=None,
  max_price_cents=None, min_rating=None, sort=None, page=1, page_size=20) -> SearchResult`

Validação, sempre com `InvalidInputError`:
- `page`/`page_size` < 1;
- preço negativo;
- `min_price_cents > max_price_cents`;
- `min_rating` fora de 0..5;
- `sort` fora de `relevance | price_asc | price_desc | rating` (ignorando maiúsculas).
  Vazio/`None` = `relevance`.

Algoritmo:
1. Busca os candidatos com os filtros estruturais.
2. Se `query` tiver termos (`ranker.query_terms`), aplica `ranker.rank`. Se o resultado for
   vazio, tenta `ranker.correct_terms` com `ranker.vocabulary(candidatos)`. Se a correção
   achar algo, usa esse resultado e preenche `corrected_query` (termos corrigidos unidos por
   espaço). Sem termos, os candidatos ficam em ordem de `id`.
3. Ordena conforme `sort`:
   - `price_asc`: preço, depois id;
   - `price_desc`: preço desc, depois id;
   - `rating`: nota desc, `review_count` desc, depois id;
   - `relevance`: mantém a ordem do passo 2.
4. Pagina. `total` é o total depois dos filtros.

**router.py**: registrar em `main.py` com o prefixo `/api/search`.

- `GET /products?q=&category=&min_price_cents=&max_price_cents=&min_rating=&sort=&page=1&page_size=20`
  → **200** `{items, total, page, page_size, corrected_query}`. `page >= 1` e
  `1 <= page_size <= 100` (senão **422**). Erros do service → **400**.

`schemas.py` define a própria `SearchOut` e o formato dos itens. **Não** importe
`catalog.schemas`: copie os campos de `ProductOut`.
