# SPEC — Mercatto v2 (local LLM)

Marketplace estilo Amazon. Experimento: medir o que um LLM local (~35B) consegue construir
resolvendo issues pequenas, uma de cada vez. Stack: React + TS (front), Python + FastAPI (back),
SQLite. Arquitetura e módulos reaproveitados da parte 1 (`amazon-clone`, Java/Spring).

## Funcionalidades

1. Contas: cadastro (comprador ou vendedor), login com JWT, perfil e troca de senha
2. Catálogo: produtos, categorias, estoque; CRUD do vendedor; produtos relacionados
3. Busca: texto livre com relevância e correção de typo, filtros e ordenação
4. Carrinho: itens, quantidade, "salvar para depois"
5. Pedidos: checkout com pagamento simulado (mock), retentativa, endereço, rastreio de envio
6. Avaliações: nota de 1 a 5, nota média no produto, "útil"
7. Painel do vendedor: inventário, pedidos recebidos, avanço do envio, métricas

## Fora de escopo

Pagamento/envio reais, listas de desejos, recomendações da home, fotos/vídeos em avaliações.

## Fluxo

Cada issue fica em `docs/issues/NN-slug.md`, com os testes que a definem em
`backend/tests/test_issue_NN_*.py` (01–21) ou `frontend/src/__tests__/issue_NN_*.test.tsx`
(22–30), escritos por humanos; o modelo não pode alterá-los.
O modelo resolve uma issue por vez: `python harness/run.py NN`. O harness injeta no prompt só as
assinaturas públicas dos arquivos `provides` das issues listadas em `depends`.
