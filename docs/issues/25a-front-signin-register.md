---
id: 25a-front-signin-register
title: "front: entrar e criar conta (parte 1 da issue 25)"
depends: [22-front-scaffold, 23-front-design]
provides: [frontend/src/pages/SignIn.tsx, frontend/src/pages/Register.tsx]
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, frontend/src/components/ui/Button.tsx, frontend/src/components/ui/Button.css, frontend/src/components/ui/Input.tsx, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_25a_signin_register.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_25a_signin_register.test.tsx src/__tests__/issue_24a_layout_home.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 4
---
# front: entrar e criar conta (parte 1 da issue 25)

Os testes estão em `frontend/src/__tests__/issue_25a_signin_register.test.tsx` e **não podem ser alterados**. Esta issue
troca os placeholders de `src/pages/SignIn.tsx` e `src/pages/Register.tsx`. Use `useAuth()` (de
`../auth/AuthContext`: `login(email, password)` e `register({ name, email, password, role })`,
que repassam o `ApiError` em caso de erro) e os componentes de `components/ui`.

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

## Formulários

Use `<form noValidate>`: a validação é a desta issue, e não a do navegador (com `required` ou
`minLength`, o navegador bloquearia o envio com o balão dele, e a mensagem daqui não apareceria).
Os erros de campo vão na prop `error` do `Input`.

## Entrar (`/signin`)

- Campos "Email" e "Password" e botão "Sign in" (com `loading` enquanto envia).
- Sucesso → navega para o parâmetro `next` da URL ou para `/`.
- Erro 401 → `ErrorMessage` com o texto "Incorrect email or password".
- Link "Create account" para `/register`, preservando o `next` (`/register?next=...`).
- Já logado ao abrir a página → redireciona para `/`.

## Criar conta (`/register`)

- Campos "Name", "Email", "Password" e "Confirm password". Abaixo da senha, a dica
  "At least 8 characters".
- Um `<fieldset>` com `<legend>Account type</legend>` e dois rádios: "I want to buy" (`BUYER`,
  marcado por padrão) e "I want to sell" (`SELLER`).
- Botão "Create account".
- Validação antes de enviar, com o erro no próprio campo (e sem chamar a API):
  - senha com menos de 8 caracteres → "Password must be at least 8 characters" no campo Password;
  - senhas diferentes → "Passwords do not match" no campo Confirm password.
- Erro 409 → no campo Email: "This email is already registered".
- Sucesso → já entra (o `register` do contexto faz login) e navega para `next` ou `/`.
