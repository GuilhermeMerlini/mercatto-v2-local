---
id: 25-front-auth-account
title: "front: entrar, criar conta e minha conta"
depends: [22-front-scaffold, 23-front-design]
provides: []
context_files: [frontend/DESIGN.md, frontend/src/styles/tokens.css, backend/app/modules/users/schemas.py, frontend/src/__tests__/issue_25_auth_account.test.tsx]
test_cmd: python harness/export_openapi.py > frontend/openapi.json && cd frontend && npm install --no-audit --no-fund --silent && npm run gen:api && npm run build && npx vitest run src/__tests__/issue_25_auth_account.test.tsx
max_iters: 5
---
# front: entrar, criar conta e minha conta

Os testes estão em `frontend/src/__tests__/issue_25_auth_account.test.tsx` e **não podem ser
alterados**. Use `useAuth()` e os componentes de `components/ui`.

## Entrar (`/signin`)

- Campos "Email" e "Senha" e botão "Entrar" (com `loading` enquanto envia).
- Sucesso → navega para o parâmetro `next` da URL ou para `/`.
- Erro 401 → `ErrorMessage` com o texto "Email ou senha incorretos".
- Link "Criar conta" para `/register`, preservando o `next`.
- Já logado → redireciona para `/`.

## Criar conta (`/register`)

- Campos "Nome", "Email", "Senha" (dica: mínimo de 8 caracteres) e "Confirmar senha".
- Um grupo de rádio "Tipo de conta" com as opções "Quero comprar" (`BUYER`, padrão) e "Quero
  vender" (`SELLER`).
- Validação no cliente antes de enviar, com o erro no próprio campo:
  - senha com menos de 8 → "A senha precisa ter pelo menos 8 caracteres";
  - senhas diferentes → "As senhas não conferem".
- Erro 409 → erro no campo Email: "Este email já está cadastrado".
- Sucesso → já entra (o `register` do contexto faz login) e navega para `next` ou `/`.

## Minha conta (`/account`)

- Seção "Dados pessoais": Nome e Email preenchidos com o usuário atual e botão "Salvar"
  (`PATCH /api/users/me`).
  - Sucesso → mensagem "Dados atualizados" (`role="status"`) e atualiza o usuário no contexto.
    Para isso, acrescente `refreshUser()` ao `AuthContext`.
  - 409 → erro no Email.
- Seção "Alterar senha": "Senha atual", "Nova senha" e "Confirmar nova senha", com botão
  "Alterar senha" (`PUT /api/users/me/password`).
  - Sucesso → "Senha alterada" e limpa os campos.
  - 400 → erro no campo "Senha atual" com o `detail` da API. **Não** deslogue: 400 não é 401.
