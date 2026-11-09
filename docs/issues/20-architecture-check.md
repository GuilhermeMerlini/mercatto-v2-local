---
id: 20-architecture-check
title: "Arquitetura: módulos só se falam via service, sem ciclos"
depends: [17-sellers-dashboard, 18-catalog-related, 16-reviews-helpful, 11-cart-save-for-later, 09-search-service]
provides: []
context_files: [docs/ARCHITECTURE.md, backend/tests/test_issue_20_architecture.py]
test_cmd: cd backend && python -m pytest tests/test_issue_20_architecture.py -q
max_iters: 3
---
# Arquitetura: módulos só se falam via service, sem ciclos

Os testes estão em `backend/tests/test_issue_20_architecture.py` e **não podem ser alterados**.
Eles leem (via `ast`) todos os arquivos de `backend/app/modules/` e verificam:

1. Um módulo só importa outro via `app.modules.<outro>.service`.
2. As dependências entre módulos respeitam o grafo de `docs/ARCHITECTURE.md` (sem ciclos).
3. Nenhum `service.py` importa `fastapi`/`starlette`.
4. Nenhum `router.py` lança `HTTPException`.
5. Nenhum `models.py` usa `Relationship`.

`modules/registry.py` é a única exceção à regra 1.

Rode os testes. Para cada violação apontada, corrija o código (mova o tipo para o `service.py`
dono, reexporte-o pelo service ou duplique o schema no módulo que consome). **Não mude o
comportamento**: todos os testes `tests/test_issue_*` precisam continuar passando
(`python -m pytest -q`).
