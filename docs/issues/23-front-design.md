---
id: 23-front-design
title: "front: direção visual (DESIGN.md), tokens e componentes base"
depends: [22-front-scaffold]
provides: [frontend/src/components/ui/index.ts]
context_files: [docs/SPEC.md, frontend/src/main.tsx, frontend/src/__tests__/issue_23_design.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_23_design.test.tsx
max_iters: 5
---
# front: direção visual (DESIGN.md), tokens e componentes base

Os testes estão em `frontend/src/__tests__/issue_23_design.test.tsx` e **não podem ser
alterados**. Eles verificam comportamento e acessibilidade, não aparência. **O design é
decisão sua.**

## Briefing

Mercatto é um marketplace generalista: livros, eletrônicos, casa, moda, brinquedos. A
identidade é **original**: não imite a Amazon nem outro varejista (cores, logo, layout de
cabeçalho). Escolha uma personalidade e mantenha a coerência em todo o produto.

Restrições:
- Contraste WCAG AA (texto normal ≥ 4.5:1). Foco sempre visível (`:focus-visible`).
- Funciona de 360px a 1440px, sem scroll horizontal.
- Respeita `prefers-reduced-motion`.
- Só CSS (variáveis CSS e um arquivo `.css` por componente ou CSS modules). Nenhuma biblioteca
  de componentes ou de CSS. Fontes do sistema ou no máximo uma família do Google Fonts.
- Toda cor, espaçamento, raio, sombra e tipografia vem de token. Nada de valor solto nos
  componentes.

## Criar

1. **`frontend/DESIGN.md`**: a direção visual, escrita para as próximas issues seguirem.
   - personalidade em 2–3 frases;
   - paleta (tokens e uso de cada um);
   - escala tipográfica;
   - espaçamento;
   - raios e sombras;
   - movimento;
   - regras de composição: como é um card de produto, como se mostra preço com desconto, como
     são estados vazios e erros;
   - o que **não** fazer.

   Máximo de ~120 linhas.
2. **`src/styles/tokens.css`**: os tokens em `:root`. **`src/styles/global.css`**: reset leve,
   tipografia base e foco. Os dois importados em `main.tsx`.
3. **`src/components/ui/`**, com `index.ts` exportando tudo:
   - `Button`: props `variant: "primary" | "secondary" | "ghost"` (padrão `primary`) e
     `loading`. Com `loading`, fica desabilitado e tem `aria-busy="true"`. Repassa as demais
     props de `<button>`.
   - `Input` e `Select`: prop `label` **obrigatória**, ligada via `htmlFor`/`id` (gere o `id` com
     `useId`). Prop `error?: string`, mostrada abaixo do campo e ligada por `aria-describedby`,
     com `aria-invalid="true"`.
   - `Card`: contêiner simples (`as?: "div" | "article" | "section"`).
   - `Price({ cents, listCents? })`: usa `formatCents`. Se `listCents > cents`, mostra também o
     preço antigo riscado (`<s>`) e o desconto em % arredondado (`"-25%"`).
   - `StarRating({ value, count? })`: um elemento com `role="img"` e
     `aria-label="Nota 4,5 de 5"` (uma casa decimal, vírgula). Se `count` vier, mostra
     `"(12)"` ao lado.
   - `Spinner`: `role="status"` com texto acessível `"Carregando"`.
   - `EmptyState({ title, children? })`
   - `ErrorMessage({ children })`: `role="alert"`.
   - `Pagination({ page, total, pageSize, onChange })`: botões "Anterior" e "Próxima", este
     desabilitado na última página e "Anterior" na primeira. Texto `"Página 2 de 5"`. Não
     renderiza nada se houver uma página só.
