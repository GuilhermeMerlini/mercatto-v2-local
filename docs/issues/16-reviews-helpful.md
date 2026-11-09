---
id: 16-reviews-helpful
title: "reviews: marcar avaliação como útil"
depends: [15-reviews-create-list]
provides: [backend/app/modules/reviews/service.py]
context_files: [backend/app/modules/reviews/models.py, backend/app/modules/reviews/service.py, backend/app/modules/reviews/router.py, backend/tests/conftest.py, backend/tests/test_issue_16_reviews_helpful.py]
test_cmd: cd backend && python -m pytest tests/test_issue_16_reviews_helpful.py tests/test_issue_15_reviews_create_list.py -q
max_iters: 4
---
# reviews: marcar avaliação como útil

Os testes estão em `backend/tests/test_issue_16_reviews_helpful.py` e **não podem ser alterados**.

## Nova função em `reviews/service.py`

`mark_helpful(session, review_id) -> ReviewView`: incrementa `helpful_count` com um `UPDATE`
atômico (`helpful_count = helpful_count + 1`). Ler e somar perde votos concorrentes. Avaliação
inexistente → `NotFoundError`.

## Novo endpoint

`POST /api/reviews/{review_id}/helpful` (público) → **200** com a avaliação atualizada ou **404**.
