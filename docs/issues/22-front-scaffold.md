---
id: 22-front-scaffold
title: "front: projeto Vite + React + TS, cliente da API, autenticação e rotas"
depends: [21-integration-flow]
provides: [frontend/src/api/client.ts, frontend/src/api/token.ts, frontend/src/api/types.ts, frontend/src/auth/AuthContext.tsx, frontend/src/auth/RequireAuth.tsx, frontend/src/lib/money.ts, frontend/src/App.tsx]
context_files: [docs/SPEC.md, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_22a_api.test.ts, frontend/src/__tests__/issue_22b_auth_routes.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_22a_api.test.ts src/__tests__/issue_22b_auth_routes.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: projeto Vite + React + TS, cliente da API, autenticação e rotas

Dividida em **22a** (`src/api/` e `src/lib/`) e **22b** (`src/auth/`, `App.tsx`, `main.tsx` e páginas).
Os testes estão em `frontend/src/__tests__/issue_22a_api.test.ts` e
`issue_22b_auth_routes.test.tsx` e **não podem ser alterados**. A interface é em **português do Brasil**. Esta issue **não** define visual: as
páginas são só placeholders (o design vem na issue 23).

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

## `src/auth/`

- `AuthContext.tsx`: `AuthProvider` e `useAuth()`, que devolve
  `{ user: User | null, loading: boolean, login(email, password), register({name, email,
  password, role}), logout() }`.
  - `login` chama `POST /api/users/login`, guarda o token e define `user`.
  - `register` chama `POST /api/users/register` e depois `login`.
  - Erros da API em `login` e `register` são propagados (`ApiError`), para a página mostrar.
  - `logout` limpa token e usuário.
  - Ao montar com token salvo, carrega `GET /api/users/me` (`loading` fica verdadeiro até
    terminar; erro → `logout`).
  - Registra `onUnauthorized(logout)`.
- `RequireAuth.tsx`: `<RequireAuth role?="SELLER">{children}</RequireAuth>`.
  - Enquanto `loading`, não renderiza nada.
  - Sem usuário, redireciona para `/signin?next=<rota atual>`.
  - Com papel errado, redireciona para `/`.

## `src/lib/money.ts`

`formatCents(cents: number): string` → `Intl.NumberFormat("pt-BR", { style: "currency",
currency: "BRL" })` sobre `cents / 100` (`1320` → `"R$ 13,20"`).

## `src/App.tsx`

Rotas com `react-router-dom`. Cada página fica em `src/pages/<Nome>.tsx` e por ora só mostra um
`<h1>` com o nome:
- `/` (Home), `/search` (Busca), `/products/:id` (Produto), `/signin` (Entrar),
  `/register` (Criar conta);
- `/cart` (Carrinho), `/checkout` (Finalizar compra), `/orders` (Meus pedidos),
  `/orders/:id` (Pedido), `/account` (Minha conta): todas com `RequireAuth`;
- `/seller` (Painel do vendedor): `RequireAuth role="SELLER"`;
- `*` (Página não encontrada).

`App` envolve tudo em `AuthProvider`. Exports: `App` é `export default`; `AuthProvider`, `useAuth`
e `RequireAuth` são exports nomeados. `main.tsx` monta `<BrowserRouter><App/></BrowserRouter>`,
então **`App` não cria o router** (os testes o montam dentro de um `MemoryRouter`).
