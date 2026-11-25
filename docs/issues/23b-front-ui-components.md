---
id: 23b-front-ui-components
title: "front: componentes de exibição (parte 2 da issue 23)"
depends: [23a-front-design-base, 22a-front-api]
provides: [frontend/src/components/ui/index.ts]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/ui/index.ts, frontend/src/__tests__/issue_23b_ui_components.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_23a_design_base.test.tsx src/__tests__/issue_23b_ui_components.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: componentes de exibição (parte 2 da issue 23)

Os testes estão em `frontend/src/__tests__/issue_23b_ui_components.test.tsx` e **não podem ser
alterados**. Eles verificam comportamento e acessibilidade, não aparência. Os testes da 23a
também rodam e precisam continuar passando.

O `DESIGN.md`, os tokens (`src/styles/tokens.css`) e os componentes `Button`, `Input`, `Select` e
`Card` já existem (issue 23a). **Siga o `DESIGN.md`** e use só os tokens que existem; se precisar
de um token novo, acrescente em `tokens.css` sem mudar os outros. Não reescreva os componentes
da 23a.

Restrições (as mesmas da 23a): contraste WCAG AA, foco visível, respeito a
`prefers-reduced-motion` (inclusive na animação do `Spinner`), só CSS, e toda cor, espaçamento,
raio, sombra e tipografia vem de token. Nenhuma cor solta (hex, `rgb()`, `hsl()`) nos arquivos de
`src/components/ui/`.

## Criar em `src/components/ui/`

Acrescente cada um ao `index.ts`, mantendo os exports da 23a:

- `Price({ cents, listCents? })`: usa `formatCents`. Se `listCents > cents`, mostra também o
  preço antigo riscado (`<s>`) e o desconto em % arredondado (`"-25%"`).
- `StarRating({ value, count? })`: um elemento com `role="img"` e
  `aria-label="Nota 4,5 de 5"` (uma casa decimal, vírgula). Se `count` vier, mostra
  `"(12)"` ao lado.
- `Spinner`: `role="status"` com texto acessível `"Carregando"`.
- `EmptyState({ title, children? })`: o `title` vai num heading (`<h2>`).
- `ErrorMessage({ children })`: `role="alert"`.
- `Pagination({ page, total, pageSize, onChange })`: botões "Anterior" e "Próxima", este
  desabilitado na última página e "Anterior" na primeira. Texto `"Página 2 de 5"`. Não
  renderiza nada se houver uma página só.
