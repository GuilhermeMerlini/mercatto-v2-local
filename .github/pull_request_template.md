## Issue NN — <título da issue>

<!-- Um parágrafo: o que a issue entrega e o que já dá para fazer com ela. -->

### Divisão da issue
<!-- Apague se a issue não foi dividida. -->
A issue NN foi dividida em duas partes, uma por arquivo de teste:
- **NNa** (`docs/issues/NNa-<slug>.md`): <o que cobre>, com N testes.
- **NNb** (`docs/issues/NNb-<slug>.md`): <o que cobre>, com N testes. Roda também os testes da NNa.

A `NN-<slug>.md` original passa a apontar para os dois arquivos de teste.

<!-- O que as issues ganharam depois da primeira rodada (avisos, contexto, dicas). -->

### O que entra
- **<Página, módulo ou componente>**
  - <comportamento>
  - <códigos de erro e o que aparece>

### Resultado do harness
Modelo `<modelo>`.

| Execução | Tentativas | Resultado | Tokens (prompt / gerados) | Tempo |
|---|---|---|---|---|
| NNa | N | **aprovado** / reprovado (X de Y) | N / N | N s |
| NNa (`--continue --hint`) | N | **aprovado** | N / N | N s |

<!-- Onde o modelo errou e o que a dica corrigiu. -->

### Correções manuais
<!-- O que foi corrigido à mão e por quê, por parte. Diga quais pontos os testes não cobrem. "Nenhuma" se não houve. -->
- **NNa**
  - <correção>

### Problemas conhecidos
<!-- Apague se não houver. Aponte as issues em que ficaram registrados. -->

### Testes
<!-- Arquivos novos e quantos testes cada um tem. -->
Arquivos novos: `<arquivo>` (N). Nenhum teste existente foi alterado, então o PR não precisa do label `edita-testes`.

### Como testar
<!-- Issue de backend: cd backend && ../.venv/bin/python -m pytest tests/test_issue_NN_<slug>.py -q -->
    python harness/export_openapi.py > frontend/openapi.json
    cd frontend && npm ci && npm run gen:api
    npx vitest run src/__tests__    # N passed
    npm run build

Para ver no navegador:

    cd backend && uvicorn app.main:app --reload
    cd frontend && npm run dev      # http://localhost:5173/<rota>

Closes #NN
