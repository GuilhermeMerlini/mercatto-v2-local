---
id: 25b-front-account
title: "front: minha conta (parte 2 da issue 25)"
depends: [25a-front-signin-register]
provides: [frontend/src/pages/Account.tsx, frontend/src/auth/AuthContext.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/auth/AuthContext.tsx, frontend/src/pages/Register.tsx, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_25b_account.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_25a_signin_register.test.tsx src/__tests__/issue_25b_account.test.tsx src/__tests__/issue_24a_layout_home.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: minha conta (parte 2 da issue 25)

Os testes estão em `frontend/src/__tests__/issue_25b_account.test.tsx` e **não podem ser alterados**. Os testes da 25a
também rodam e precisam continuar passando. Esta issue troca o placeholder de
`src/pages/Account.tsx` e acrescenta `refreshUser()` ao `AuthContext`. Siga o padrão do
`Register.tsx` (formulário, erros de campo, `noValidate`).

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

**Estilos:** não há Tailwind nem nenhuma biblioteca de CSS no projeto. Cada componente ou página
tem o seu `.css`, importado no `.tsx`, com classes próprias que usam só `var(--token)` de
`tokens.css` (veja `Button.tsx` e `Button.css`). Um teste da 24a, que continua rodando, confere que **toda `className` usada em
`src/` existe em algum `.css`**.

## API dos componentes de `components/ui` (importe de `../components/ui`)

- `Button`: props de `<button>` + `variant?: "primary" | "secondary" | "ghost"`, `loading?: boolean`.
- `Input` / `Select`: props de `<input>` / `<select>` + `label: string` (obrigatório), `error?: string`.
- `Card`: `as?: "div" | "article" | "section"`, `children`.
- `Price`: `cents: number`, `listCents?: number | null`.
- `StarRating`: `value: number`, `count?: number`.
- `Spinner`, `ErrorMessage({ children })`, `EmptyState({ title, children? })`.
- `Pagination`: `page`, `total`, `pageSize`, `onChange(page: number)`.

## `AuthContext`: `refreshUser()`

Acrescente `refreshUser(): Promise<void>` ao valor de `useAuth()`: recarrega `GET /api/users/me` e
atualiza o `user`. Não mude o resto do contexto.

## Minha conta (`/account`)

A página tem duas seções, cada uma um `<section aria-labelledby="...">` com um `<h2>` de título
(é assim que os testes as encontram).

- Seção "Personal details": campos "Name" e "Email" preenchidos com o usuário atual e botão
  "Save" (`PATCH /api/users/me` com `{ name, email }`).
  - Sucesso → chama `refreshUser()` (o nome no cabeçalho muda) e mostra "Details updated" num
    elemento com `role="status"`.
  - 409 → no campo Email: "This email is already registered".
- Seção "Change password": campos "Current password", "New password" e "Confirm new password", e
  o botão "Change password" (`PUT /api/users/me/password` com
  `{ current_password, new_password }`; sucesso é 204, sem corpo).
  - Confirmação diferente → "Passwords do not match" no campo Confirm new password, sem chamar a
    API.
  - Sucesso → "Password changed" e limpa os três campos.
  - 400 → no campo "Current password", com o `detail` da API. **Não** deslogue: 400 não é 401.
