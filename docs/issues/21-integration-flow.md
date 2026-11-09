---
id: 21-integration-flow
title: "Integração: fluxo completo de compra"
depends: [20-architecture-check, 19-seed]
provides: []
context_files: [backend/app/main.py, backend/tests/conftest.py, backend/tests/test_issue_21_integration_flow.py]
test_cmd: cd backend && python -m pytest -q
max_iters: 4
---
# Integração: fluxo completo de compra

Os testes estão em `backend/tests/test_issue_21_integration_flow.py` e **não podem ser
alterados**. Eles percorrem a API de ponta a ponta, só por HTTP:

1. Vendedor se cadastra e cria produtos; comprador se cadastra.
2. Comprador busca, abre o produto e vê os relacionados.
3. Comprador adiciona ao carrinho, salva um item para depois e faz o checkout (aprovado).
4. Estoque baixou, o pedido aparece no histórico e o vendedor vê o pedido.
5. Vendedor avança o envio até `DELIVERED`. O endereço não pode mais ser trocado (409).
6. Comprador avalia, e a nota média aparece no produto e na busca ordenada por `rating`.
7. Um pagamento recusado (gateway em `first-attempt`) devolve o estoque, e a nova tentativa paga.

Esta issue não pede código novo: rode **todos** os testes (`python -m pytest -q`) e corrija o que
o fluxo integrado revelar. Os testes das outras issues também precisam passar.
