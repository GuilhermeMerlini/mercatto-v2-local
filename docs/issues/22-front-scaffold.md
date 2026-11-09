---
id: 22-front-scaffold
title: "front: projeto Vite + React + TS, cliente da API, autenticação e rotas"
depends: [21-integration-flow]
provides: [frontend/src/api/client.ts, frontend/src/api/token.ts, frontend/src/api/types.ts, frontend/src/auth/AuthContext.tsx, frontend/src/auth/RequireAuth.tsx, frontend/src/lib/money.ts, frontend/src/App.tsx]
context_files: [docs/SPEC.md, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_22_scaffold.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_22_scaffold.test.tsx
max_iters: 5
---
# front: projeto Vite + React + TS, cliente da API, autenticação e rotas

Os testes estão em `frontend/src/__tests__/issue_22_scaffold.test.tsx` e **não podem ser
alterados**. A interface é em **português do Brasil**. Esta issue **não** define visual: as
páginas são só placeholders (o design vem na issue 23).

## Projeto (`frontend/`)

`package.json` com versões **exatas** (sem `^`):
- dependências: `react@18.3.1`, `react-dom@18.3.1`, `react-router-dom@6.28.0`;
- desenvolvimento: `typescript@5.6.3`, `vite@5.4.11`, `@vitejs/plugin-react@4.3.4`,
  `vitest@2.1.8`, `jsdom@25.0.1`, `@testing-library/react@16.1.0`, `@testing-library/dom@10.4.0`,
  `@testing-library/user-event@14.5.2`, `@testing-library/jest-dom@6.6.3`,
  `openapi-typescript@7.4.4`, `@types/react@18.3.12`, `@types/react-dom@18.3.1`.

Scripts:
- `dev`: `vite`;
- `build`: `tsc -b && vite build`;
- `test`: `vitest run`;
- `gen:api`: `openapi-typescript openapi.json -o src/api/schema.d.ts`.

Também criar:
- `tsconfig.json` com `strict: true`;
- `vite.config.ts` com o plugin react e `test: { environment: "jsdom", setupFiles:
  "./src/setupTests.ts", globals: true }`;
- `index.html`;
- `src/main.tsx`;
- `src/setupTests.ts`, que importa `@testing-library/jest-dom/vitest`;
- `.gitignore` com `node_modules`, `dist`, `openapi.json` e `src/api/schema.d.ts`.

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

`App` envolve tudo em `AuthProvider`. `main.tsx` monta `<BrowserRouter><App/></BrowserRouter>`,
então **`App` não cria o router** (os testes o montam dentro de um `MemoryRouter`).
