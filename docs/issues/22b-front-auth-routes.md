---
id: 22b-front-auth-routes
title: "front: autenticação, rotas e páginas placeholder (parte 2 da issue 22)"
depends: [22a-front-api]
provides: [frontend/src/auth/AuthContext.tsx, frontend/src/auth/RequireAuth.tsx, frontend/src/App.tsx, frontend/src/main.tsx]
context_files: [docs/SPEC.md, frontend/src/api/types.ts, frontend/src/__tests__/issue_22b_auth_routes.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_22a_api.test.ts src/__tests__/issue_22b_auth_routes.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: autenticação, rotas e páginas placeholder (parte 2 da issue 22)

Os testes estão em `frontend/src/__tests__/issue_22b_auth_routes.test.tsx` e **não podem ser
alterados**. A interface é em **português do Brasil**. Esta issue **não** define visual: as
páginas são só placeholders (o design vem na issue 23).

`src/api/` e `src/lib/money.ts` já existem (issue 22a): use `api`, `onUnauthorized`, `getToken`,
`setToken`, `clearToken` e os tipos de `src/api/types.ts` sem reescrevê-los. O esqueleto
(`package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/setupTests.ts`) também já
existe: não altere nem adicione dependências.

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
