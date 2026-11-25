---
id: 22a-front-api
title: "front: cliente da API, token e formatação de dinheiro (parte 1 da issue 22)"
depends: [19-seed]
provides: [frontend/src/api/client.ts, frontend/src/api/token.ts, frontend/src/api/types.ts, frontend/src/lib/money.ts]
context_files: [docs/SPEC.md, frontend/package.json, frontend/tsconfig.json, frontend/src/__tests__/issue_22a_api.test.ts]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npx tsc -b && npx vitest run src/__tests__/issue_22a_api.test.ts
max_iters: 4
---
# front: cliente da API, token e formatação de dinheiro (parte 1 da issue 22)

Os testes estão em `frontend/src/__tests__/issue_22a_api.test.ts` e **não podem ser alterados**.
Esta parte só cria código TypeScript sem React: autenticação, rotas e páginas ficam na 22b.
Crie **apenas** os 4 arquivos abaixo (`src/main.tsx` e `src/App.tsx` ainda não existem; o teste
roda `tsc -b`, não o build do Vite).

## Esqueleto (já existe, não altere)

`package.json` (versões exatas e scripts `dev`, `build`, `test`, `gen:api`), `package-lock.json`,
`tsconfig.json` (`strict: true`), `vite.config.ts`, `index.html`, `src/setupTests.ts` e
`.gitignore` já estão commitados. Não adicione dependências.

`src/api/schema.d.ts` é **gerado** (`npm run gen:api`, a partir do `openapi.json` que o harness
exporta). Nunca escreva esse arquivo nem tipos da API à mão.

## `src/api/`

- `types.ts`: aliases dos schemas gerados, por exemplo
  `export type User = components["schemas"]["UserOut"]` e
  `export type LoginResponse = components["schemas"]["LoginOut"]`. Cada issue seguinte
  acrescenta os aliases de que precisa.
- `token.ts`: `getToken()`, `setToken(t)` e `clearToken()` com `localStorage` (chave
  `mercatto.token`). Envolva cada acesso em `try/catch` (o `localStorage` pode lançar erro).
- `client.ts`
  - `export class ApiError extends Error { status: number; detail: string }`
  - `export async function api<T>(path: string, init?: { method?: string; body?: unknown;
    headers?: Record<string, string> }): Promise<T>`
    - A URL é `(import.meta.env.VITE_API_URL ?? "http://localhost:8000") + path`.
    - `body` vai como JSON (`Content-Type: application/json`).
    - Se houver token, envia `Authorization: Bearer <token>`.
    - Resposta 204 → `undefined`.
    - Status não-2xx → lança `ApiError`. `detail` vem do corpo: string, ou, quando é lista (422
      do FastAPI), os `msg` unidos por `"; "`. Sem corpo JSON → `"Erro <status>"`.
    - Em 401, chama todos os callbacks registrados com
      `export function onUnauthorized(cb: () => void): () => void` (o retorno remove o
      callback).

## `src/lib/money.ts`

`formatCents(cents: number): string` → `Intl.NumberFormat("pt-BR", { style: "currency",
currency: "BRL" })` sobre `cents / 100` (`1320` → `"R$ 13,20"`).
