# Mercatto v2 — um marketplace construído por um LLM local

Experimento da parte 2 do trabalho: medir até onde um LLM **local** (~35B parâmetros, rodando
via Ollama) consegue construir um marketplace no estilo da Amazon, resolvendo **issues
pequenas, uma de cada vez**.

A divisão de trabalho é rígida:

| Humanos escrevem | O modelo escreve |
| --- | --- |
| Especificação, arquitetura e issues (`docs/`) | Todo o código de `backend/app/` (exceto o esqueleto) |
| Testes de aceite de cada issue | Todo o código de `frontend/` |
| O harness (`harness/`) | O design do front (`frontend/DESIGN.md`) |

A arquitetura e os módulos vêm da parte 1 (`amazon-clone`, Java + Spring Boot),
portados para **Python + FastAPI** no backend. O front é **React + TypeScript (Vite)**, e a
identidade visual fica a cargo do próprio modelo.

---

## Como funciona

```
docs/issues/NN-*.md ──┐
docs/ARCHITECTURE.md ─┼─► harness monta o prompt ─► LLM local ─► arquivos gravados
API das dependências ─┘            ▲                                    │
                                   │                                    ▼
                                   └──── saída dos testes ◄──── roda test_cmd da issue
                                         (até max_iters vezes; passou → fim)
```

Cada issue é um arquivo Markdown com um cabeçalho YAML:

```yaml
---
id: 13-orders-checkout
title: "orders: checkout com reserva de estoque e pagamento"
depends: [07-catalog-stock, 12-payments-mock]     # issues que precisam estar prontas
provides: [backend/app/modules/orders/service.py] # API pública que esta issue oferece
context_files: [...]                              # arquivos enviados inteiros ao modelo
test_cmd: cd backend && python -m pytest tests/test_issue_13_orders_checkout.py -q
max_iters: 5
---
```

O prompt de cada tentativa tem quatro partes:

1. **ARQUITETURA**: `docs/ARCHITECTURE.md`, igual para todas as issues.
2. **ISSUE**: o texto da issue.
3. **API PÚBLICA DAS DEPENDÊNCIAS**: para cada issue em `depends`, só as **assinaturas** dos
   arquivos `provides` dela (funções, dataclasses, enums, tipos), sem o corpo. Isso reduz em
   46–71% o contexto das dependências (`harness/signatures.py`).
4. **ARQUIVOS EXISTENTES RELEVANTES**: os `context_files`, inteiros (inclusive o arquivo de
   testes da issue).

O modelo responde com arquivos completos (`### FILE: caminho`), que o harness grava. Se os
testes falharem, a saída deles volta para o modelo na tentativa seguinte.

**Proteções:** o modelo nunca escreve fora do projeto, em `backend/tests/`,
`frontend/src/__tests__/`, `node_modules` ou em arquivos gerados (`schema.d.ts`, `openapi.json`,
`package-lock.json`).

---

## Estrutura

```text
mercatto-v2-local/
├── docs/
│   ├── SPEC.md            # o que o produto faz e o que está fora de escopo
│   ├── ARCHITECTURE.md    # regras do monolito modular (vai em todo prompt)
│   └── issues/            # 30 issues: 01–21 backend, 22–30 frontend
├── harness/
│   ├── run.py             # laço prompt → arquivos → testes → correção
│   ├── signatures.py      # extrai a API pública (Python via ast, TS via exports)
│   ├── export_openapi.py  # gera o OpenAPI sem subir o servidor (tipos do front)
│   └── reset.sh           # descarta tudo que não foi commitado
├── backend/
│   ├── app/
│   │   ├── core/          # config, db, erros de domínio (o resto vem nas issues 01–02)
│   │   ├── modules/       # users, catalog, search, cart, orders, payments, reviews, sellers
│   │   ├── seed_data/     # 500 produtos reais (CSV herdado da parte 1)
│   │   └── main.py
│   ├── tests/             # conftest.py + test_issue_NN_*.py (escritos por humanos)
│   └── ruff.toml
└── frontend/              # criado pelo modelo a partir da issue 22
```

Cada módulo do backend segue o mesmo formato: `models.py` (tabelas SQLModel), `schemas.py`
(entrada/saída da API), `service.py` (regras de negócio; **única** API pública do módulo) e
`router.py` (endpoints). As regras completas, como o grafo de dependências entre módulos, os
erros de domínio e o dinheiro em centavos, estão em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Setup

Requisitos:
- Python 3.10+;
- Git;
- Ollama (ou outro servidor compatível com a API da OpenAI) com o modelo baixado;
- Node 18+, só a partir da issue 22.

```bash
git clone https://github.com/GuilhermeMerlini/mercatto-v2-local.git
cd mercatto-v2-local
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r harness/requirements.txt
(cd backend && python -m pytest tests/test_health.py)   # deve passar
ollama list                                             # anote o nome exato do modelo
```

### Janela de contexto do Ollama (importante)

Os prompts têm de 5 a 9 mil tokens. Por padrão, o Ollama usa uma janela de 2–4 mil tokens e
**corta o início do prompt sem avisar**, justamente onde estão a arquitetura e a issue. Pela API
compatível com OpenAI não dá para mudar isso por requisição; configure no servidor:

```bash
OLLAMA_CONTEXT_LENGTH=32768 ollama serve
# ou crie uma variante do modelo com um Modelfile contendo:
#   FROM qwen3.6:35b
#   PARAMETER num_ctx 32768
# e rode: ollama create qwen35b-32k -f Modelfile
```

Confira com `ollama show <modelo>`.

---

## Resolvendo uma issue

```bash
source .venv/bin/activate
export LLM_BASE_URL=http://localhost:11434/v1     # padrão; ajuste se o modelo estiver em outro host
python harness/run.py 1 --model qwen3.6:35b       # issue 01 (aceita 1, 01 ou o caminho do .md)
```

O ciclo de cada issue:

1. **Rodar**: `python harness/run.py N --model <modelo>`.
2. **Revisar**: `git diff`. Passar nos testes não garante código bom; leia o que o modelo fez.
3. **Se passou**: `git add -A && git commit -m "Issue NN (<modelo>, K tentativas)" && git push`.
4. **Se não passou**, há três caminhos:
   - `python harness/run.py N --continue`: retoma a partir dos arquivos e do erro da última
     tentativa, sem apagar nada;
   - `harness/reset.sh`: volta ao último commit e tenta do zero;
   - se o modelo trava sempre no mesmo ponto, a issue provavelmente está grande demais.
     Divida-a, em vez de aumentar `max_iters`, e registre isso como resultado.

Variáveis de ambiente do harness:

| Variável | Padrão | Uso |
| --- | --- | --- |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Endpoint compatível com OpenAI |
| `LLM_MODEL` | `qwen3:8b` | Modelo, quando `--model` não é passado |
| `LLM_API_KEY` | `local` | Só se o servidor exigir |
| `LLM_TEMPERATURE` | `0.2` | Temperatura das respostas |

Cada execução acrescenta uma linha a `docs/results.jsonl`, com issue, modelo, tentativas, se
passou, tokens, tamanho do prompt e tempo. **Esse arquivo está no `.gitignore`**: copie-o para
fora do servidor antes de apagar o clone, ou ele se perde.

---

## Mapa das issues

Siga a ordem numérica: nenhuma issue depende de outra com número maior. As que não têm
dependências (01, 02, 08 e 12) servem de aquecimento.

| # | Issue | Depende de |
| --- | --- | --- |
| 01 | Core: hash de senha, JWT e usuário autenticado | — |
| 02 | App: handler de erros de domínio, CORS e registro de models | — |
| 03 | users: cadastro e login | 01, 02 |
| 04 | users: perfil (`/me`) e troca de senha | 03 |
| 05 | catalog: produto e CRUD do vendedor | 01, 03 |
| 06 | catalog: listagem paginada, categorias e consultas | 05 |
| 07 | catalog: estoque atômico e nota agregada | 05 |
| 08 | search: ranker de texto (puro) | — |
| 09 | search: busca com filtros, ordenação e correção de typo | 06, 08 |
| 10 | cart: carrinho e itens | 06 |
| 11 | cart: salvar para depois | 10 |
| 12 | payments: gateway mock | — |
| 13 | orders: checkout com reserva de estoque e pagamento | 07, 12 |
| 14 | orders: consulta, troca de endereço e nova tentativa de pagamento | 13 |
| 15 | reviews: criar e listar, atualizando a nota do produto | 07, 03 |
| 16 | reviews: marcar como útil | 15 |
| 17 | sellers: inventário, pedidos recebidos, envio e métricas | 06, 14 |
| 18 | catalog: produtos relacionados | 06 |
| 19 | Seed: usuários e produtos de exemplo | 03, 05 |
| 20 | Arquitetura: módulos só se falam via service | 09, 11, 16, 17, 18 |
| 21 | Integração: fluxo completo de compra | 19, 20 |
| 22 | front: projeto, cliente da API, autenticação e rotas | 21 |
| 23 | front: direção visual (`DESIGN.md`), tokens e componentes base | 22 |
| 24 | front: layout, home e busca | 22, 23 |
| 25 | front: entrar, criar conta e minha conta | 22, 23 |
| 26 | front: página do produto, relacionados e avaliações | 24, 25 |
| 27 | front: carrinho | 26 |
| 28 | front: checkout e confirmação | 27 |
| 29 | front: meus pedidos e detalhes do pedido | 28 |
| 30 | front: painel do vendedor | 29 |

**Estado dos testes:**
- **01–21:** prontos. Foram validados contra uma implementação de referência (todos passam) e
  contra o esqueleto (todos falham).
- **22–30:** ainda não escritos. Serão escritos depois que o modelo gerar o scaffold (22) e o
  `DESIGN.md` (23), e só testam comportamento e acessibilidade, nunca aparência. Revise o
  `DESIGN.md` gerado na issue 23 antes de seguir para a 24.

---

## Rodando a aplicação

Depois que as issues de backend estiverem prontas:

```bash
cd backend
python -m app.seed                          # issue 19: 3 usuários + até 500 produtos
uvicorn app.main:app --reload               # API em http://localhost:8000, docs em /docs
```

Usuários do seed (senha `mercatto123`): `seller1@mercatto.dev`, `seller2@mercatto.dev` e
`buyer@mercatto.dev`.

Depois das issues de front:

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```

---

## Problemas comuns

| Sintoma | Causa provável |
| --- | --- |
| O modelo ignora a issue ou responde sobre outra coisa | Janela de contexto pequena demais no Ollama: veja a seção de setup |
| `arquivos escritos: NENHUM` | A resposta não seguiu o formato `### FILE:`. Comum em modelos pequenos; tente de novo |
| `AVISO: dependências ainda não implementadas` | Uma issue de `depends` ainda não foi resolvida; volte e resolva-a |
| A issue 21 estoura o tempo | Ela roda a suíte inteira (~2,5 min); o limite por execução de testes é 5 min |
| Testes passam localmente mas falham no harness | O harness roda o `test_cmd` a partir da raiz do repositório, com o Python do ambiente ativo |
