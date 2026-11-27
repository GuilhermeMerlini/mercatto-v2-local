---
id: 25-front-auth-account
title: "front: entrar, criar conta e minha conta"
depends: [22-front-scaffold, 23-front-design]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_25a_signin_register.test.tsx, frontend/src/__tests__/issue_25b_account.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && { DEBUG_PRINT_LIMIT=1500 npx vitest run src/__tests__/issue_25a_signin_register.test.tsx src/__tests__/issue_25b_account.test.tsx; t=$?; npm run build; b=$?; [ $t -eq 0 ] && [ $b -eq 0 ]; }
max_iters: 5
---
# front: entrar, criar conta e minha conta

Dividida em **25a** (entrar e criar conta) e **25b** (minha conta). Os testes estão em
`frontend/src/__tests__/issue_25a_signin_register.test.tsx` e `issue_25b_account.test.tsx` e **não podem
ser alterados**. Use `useAuth()` e os componentes de `components/ui`.

A interface é em **inglês**: os textos entre aspas abaixo são exatos (os testes procuram por eles).

## Entrar (`/signin`)

- Campos "Email" e "Password" e botão "Sign in" (com `loading` enquanto envia).
- Sucesso → navega para o parâmetro `next` da URL ou para `/`.
- Erro 401 → `ErrorMessage` com o texto "Incorrect email or password".
- Link "Create account" para `/register`, preservando o `next`.
- Já logado → redireciona para `/`.

## Criar conta (`/register`)

- Campos "Name", "Email", "Password" (dica: "At least 8 characters") e "Confirm password".
- Um grupo de rádio "Account type" com as opções "I want to buy" (`BUYER`, padrão) e "I want to
  sell" (`SELLER`).
- Validação no cliente antes de enviar, com o erro no próprio campo:
  - senha com menos de 8 → "Password must be at least 8 characters";
  - senhas diferentes → "Passwords do not match".
- Erro 409 → erro no campo Email: "This email is already registered".
- Sucesso → já entra (o `register` do contexto faz login) e navega para `next` ou `/`.

## Minha conta (`/account`)

- Seção "Personal details": "Name" e "Email" preenchidos com o usuário atual e botão "Save"
  (`PATCH /api/users/me`).
  - Sucesso → mensagem "Details updated" (`role="status"`) e atualiza o usuário no contexto.
    Para isso, acrescente `refreshUser()` ao `AuthContext`.
  - 409 → erro no Email.
- Seção "Change password": "Current password", "New password" e "Confirm new password", com botão
  "Change password" (`PUT /api/users/me/password`).
  - Sucesso → "Password changed" e limpa os campos.
  - 400 → erro no campo "Current password" com o `detail` da API. **Não** deslogue: 400 não é 401.
