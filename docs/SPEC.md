# SPEC — Mercatto v2 (local LLM)

Marketplace estilo Amazon. Experimento: medir o que um LLM local (~35B) consegue construir
seguindo tarefas pequenas. Stack: React + TS (front), Python + FastAPI (back), SQLite.

## Funcionalidades (ordem de construção)

1. Auth: cadastro, login (JWT), perfil
2. Catálogo: produtos, categorias, estoque (inventory fica dentro de catalog)
3. Busca e filtros
4. Carrinho
5. Pedidos + checkout com pagamento simulado (mock)
6. Avaliações

## Fora de escopo

Pagamento/envio reais, painel de vendedor, recomendações.
