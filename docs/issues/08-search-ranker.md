---
id: 08-search-ranker
title: "search: ranker de texto (puro)"
depends: []
provides: [backend/app/modules/search/ranker.py]
context_files: [backend/tests/test_issue_08_search_ranker.py]
test_cmd: cd backend && python -m pytest tests/test_issue_08_search_ranker.py -q
max_iters: 4
---
# search: ranker de texto (puro)

Os testes estão em `backend/tests/test_issue_08_search_ranker.py` e **não podem ser alterados**.

Criar `backend/app/modules/search/ranker.py`: só funções puras, sem banco, sem FastAPI, sem
importar outros módulos. Os produtos são **qualquer objeto** com os atributos `id`, `name`,
`brand`, `category` e `description` (os três últimos podem ser `None`).

## Funções

- `normalize(text) -> str`: minúsculas, sem acentos (`unicodedata` NFKD, removendo
  combinantes). `None` → `""`.
- `tokenize(text) -> list[str]`: `normalize` e depois divide em tudo que não é `[a-z0-9]`,
  descartando vazios.
- `query_terms(query) -> list[str]`: tokens da busca sem as stop words
  `a an the of for and or with de da do das dos e em para com um uma`.
- `stem(token) -> str`, aplicando a primeira regra que vale:
  1. termina em `ies` e tem mais de 4 letras → troca por `y` ("batteries" → "battery");
  2. termina em `es` e tem mais de 4 letras → remove `es`;
  3. termina em `s` e tem mais de 3 letras → remove `s`;
  4. senão, igual.
- `term_matches(term, token) -> bool`: verdadeiro se `term == token`, se
  `stem(term) == stem(token)` ou, quando `term` tem 3+ letras, se `token` começa com `term`
  (ou `stem(token)` começa com `stem(term)`).
- `name_head_tokens(name) -> list[str]`: tokens do nome até o primeiro marcador de "cauda"
  (`for`, `compatible`, `with`, `fits`, `para`, `compativel`), sem incluí-lo. O marcador só
  conta depois do primeiro token.
- `score_product(product, terms) -> float | None`: `None` se algum termo não casa com nenhum
  token de nome, marca, categoria ou descrição (**todos** os termos precisam casar). Senão,
  calcula uma camada:
  - todos os termos no início do nome → 4;
  - algum termo na marca → 3;
  - todos os termos no nome → 2;
  - algum termo na categoria → 1;
  - senão → 0.

  O score é `camada + bônus de frase + 0.4 × (fração dos termos que casam no nome)`. O bônus de
  frase vale 0.5 quando há mais de um termo e `" ".join(terms)` aparece em
  `" ".join(tokenize(name))`.
- `rank(products, terms) -> list`: só os produtos com score, do maior para o menor; empate →
  `id` crescente.
- `edit_distance(a, b) -> int`: distância de Levenshtein.
- `vocabulary(products) -> set[str]`: tokens de nome, marca e categoria de todos os produtos.
- `correct_terms(terms, vocab) -> list[str] | None`
  - Cada termo com 4+ letras que não está em `vocab` (e não casa com nenhuma palavra dele via
    `term_matches`) é trocado pela palavra do vocabulário mais próxima.
  - Limite de distância: 1 edição, ou 2 se o termo tem 8+ letras.
  - Empate de distância → a palavra em ordem alfabética.
  - Termo sem palavra dentro do limite fica como está.
  - Devolve `None` se nada mudou.
