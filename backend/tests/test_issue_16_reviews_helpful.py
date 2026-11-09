import re

import pytest

from tests.conftest import BUYER, SELLER, create_product, login_user


@pytest.fixture(name="review")
def review_fixture(client):
    seller_headers, _ = login_user(client, SELLER)
    headers, _ = login_user(client, BUYER)
    product = create_product(client, seller_headers)
    r = client.post(f"/api/reviews/products/{product['id']}", json={"stars": 5, "title": "Ótimo"}, headers=headers)
    return r.json()


def test_mark_helpful_increments(client, review):
    r = client.post(f"/api/reviews/{review['id']}/helpful")
    assert r.status_code == 200
    assert r.json()["helpful_count"] == 1
    assert r.json()["id"] == review["id"]
    assert client.post(f"/api/reviews/{review['id']}/helpful").json()["helpful_count"] == 2


def test_count_shows_in_listing(client, review):
    client.post(f"/api/reviews/{review['id']}/helpful")
    listed = client.get(f"/api/reviews/products/{review['product_id']}").json()
    assert listed[0]["helpful_count"] == 1


def test_missing_review_returns_404(client):
    assert client.post("/api/reviews/999/helpful").status_code == 404


def test_helpful_is_an_atomic_increment(session, review, sql_log):
    from app.modules.reviews import service

    sql_log.clear()
    assert service.mark_helpful(session, review["id"]).helpful_count == 1
    updates = [s.lower() for s in sql_log if s.upper().startswith("UPDATE REVIEW")]
    pattern = re.compile(r'helpful_count=\(?("?review"?\.)?helpful_count\+')
    assert any(pattern.search(s.replace(" ", "")) for s in updates), (
        f"use UPDATE review SET helpful_count = helpful_count + 1; SQL executado: {sql_log}"
    )


def test_service_missing_review(session):
    from app.core.errors import NotFoundError
    from app.modules.reviews import service

    with pytest.raises(NotFoundError):
        service.mark_helpful(session, 999)
