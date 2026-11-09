---
id: 07-catalog-stock
title: "catalog: estoque atômico e nota agregada"
depends: [05-catalog-crud]
provides: [backend/app/modules/catalog/service.py]
context_files: [backend/app/modules/catalog/models.py, backend/app/modules/catalog/service.py, backend/app/core/errors.py, backend/tests/conftest.py, backend/tests/test_issue_07_catalog_stock.py]
test_cmd: cd backend && python -m pytest tests/test_issue_07_catalog_stock.py tests/test_issue_05_catalog_crud.py -q
max_iters: 4
---
# catalog: estoque atômico e nota agregada

Os testes estão em `backend/tests/test_issue_07_catalog_stock.py` e **não podem ser alterados**.
Só service: estas funções não têm endpoint (quem as chama são orders e reviews).

## Novas funções em `catalog/service.py`

- `decrease_stock(session, product_id, qty) -> None`
  - Use **um único `UPDATE` condicional**:
    `UPDATE product SET stock = stock - qty WHERE id = ? AND stock >= qty`.
    Ler, subtrair e salvar perde baixas quando há checkouts concorrentes.
  - Se nenhuma linha mudou, produto inexistente → `NotFoundError`; senão →
    `InsufficientStockError`, com o estoque intacto.
  - `qty == stock` é permitido (o estoque vai a 0). `qty <= 0` → `InvalidInputError`.
  - Faz `commit`.
- `increase_stock(session, product_id, qty) -> None`: devolve estoque (pagamento recusado),
  também com `UPDATE` atômico. Inexistente → `NotFoundError`. `qty <= 0` → `InvalidInputError`.
- `update_rating(session, product_id, average_rating, review_count) -> None`: grava a nota
  média (arredondada a 2 casas) e a contagem. O módulo reviews chama esta função depois de cada
  avaliação.

Depois de um `UPDATE` em massa, objetos já carregados na sessão ficam desatualizados: use
`session.expire_all()` ou releia o produto antes de devolver qualquer view.
