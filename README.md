# Mercatto v2 (local LLM)

Experimento: um LLM local (~35B) constrói um marketplace resolvendo issues pequenas, uma por vez.
Humano escreve `docs/` (spec, arquitetura, issues) e os testes; o modelo escreve o código.
Arquitetura e módulos vêm da parte 1 (`../amazon-clone`), portados para Python + FastAPI.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r harness/requirements.txt
cd backend && python -m pytest tests/test_health.py   # deve passar
```

## Resolver uma issue
```bash
export LLM_BASE_URL=http://localhost:11434/v1   # Ollama; ajuste p/ llama.cpp/vLLM/LM Studio
python harness/run.py 3 --model qwen3.6:35b     # issue 03 (docs/issues/03-*.md)
python harness/run.py 3 --continue              # retoma do erro anterior, sem reset
harness/reset.sh                                # descarta tudo que o modelo gerou
```
Cada issue define no front matter os arquivos de contexto, as dependências e o comando de
teste. Resultados ficam em `docs/results.jsonl`.

## Estrutura
- `docs/` contexto para o modelo: `SPEC.md`, `ARCHITECTURE.md`, `issues/`
- `harness/` laço prompt → arquivos → testes → correção
- `backend/` FastAPI modular (`app/modules/<nome>/`); testes em `tests/test_issue_NN_*.py`
- `frontend/` React + TS (Vite), a criar nas issues de front
