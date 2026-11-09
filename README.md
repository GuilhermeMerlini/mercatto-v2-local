# Mercatto v2 (local LLM)

Experimento: um LLM local (~35B) constrói um marketplace seguindo tarefas pequenas.
Humano escreve `docs/` (spec, arquitetura, tarefas); o modelo escreve o código.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r harness/requirements.txt
cd backend && python -m pytest        # deve passar (test_health)
```

## Rodar uma tarefa
```bash
export LLM_BASE_URL=http://localhost:11434/v1   # Ollama; ajuste p/ llama.cpp/vLLM/LM Studio
export LLM_MODEL=qwen3:32b                      # ajuste p/ o seu modelo
python harness/run.py docs/tasks/01-core-users.md
```
Resultados ficam em `docs/results.jsonl`; atualize `docs/PROGRESS.md` à mão.

## Estrutura
- `docs/` contexto para o modelo (SPEC, ARCHITECTURE, PROGRESS, tasks/)
- `harness/` laço prompt → arquivos → testes → correção
- `backend/` FastAPI modular (`app/modules/<nome>/`)
- `frontend/` React + TS (Vite), a criar na fase de front
