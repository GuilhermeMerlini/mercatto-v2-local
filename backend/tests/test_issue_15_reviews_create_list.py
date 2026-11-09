import pytest
from sqlmodel import SQLModel

from tests.conftest import BUYER, BUYER_2, SELLER, create_product, login_user

REVIEW_FIELDS = {"id", "product_id", "author_id", "author_name", "stars", "title", "text", "helpful_count",
                 "created_at"}


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    seller_headers, _ = login_user(client, SELLER)
    headers, uid = login_user(client, BUYER)
    product = create_product(client, seller_headers)
    return {"h": headers, "uid": uid, "p": product}


def post_review(client, headers, product_id, stars=5, title="Ótimo", text=None):
    body = {"stars": stars, "title": title, **({"text": text} if text is not None else {})}
    return client.post(f"/api/reviews/products/{product_id}", json=body, headers=headers)


def test_create_review(client, ctx):
    r = post_review(client, ctx["h"], ctx["p"]["id"], 4, "Bom", "Chegou rápido")
    assert r.status_code == 201
    body = r.json()
    assert set(body) == REVIEW_FIELDS
    assert body["author_id"] == ctx["uid"]
    assert body["author_name"] == "Ana"
    assert (body["stars"], body["title"], body["text"], body["helpful_count"]) == (4, "Bom", "Chegou rápido", 0)


def test_text_is_optional(client, ctx):
    assert post_review(client, ctx["h"], ctx["p"]["id"]).json()["text"] is None


def test_product_rating_is_updated(client, ctx):
    other, _ = login_user(client, BUYER_2)
    post_review(client, ctx["h"], ctx["p"]["id"], 5)
    post_review(client, other, ctx["p"]["id"], 4)
    product = client.get(f"/api/catalog/products/{ctx['p']['id']}").json()
    assert (product["average_rating"], product["review_count"]) == (4.5, 2)


def test_rating_is_rounded_to_two_decimals(client, ctx):
    for stars in (5, 4, 4):
        post_review(client, ctx["h"], ctx["p"]["id"], stars)
    assert client.get(f"/api/catalog/products/{ctx['p']['id']}").json()["average_rating"] == 4.33


def test_list_newest_first(client, ctx):
    first = post_review(client, ctx["h"], ctx["p"]["id"], title="Primeira").json()
    second = post_review(client, ctx["h"], ctx["p"]["id"], title="Segunda").json()
    r = client.get(f"/api/reviews/products/{ctx['p']['id']}")
    assert r.status_code == 200
    assert [x["id"] for x in r.json()] == [second["id"], first["id"]]


def test_list_is_public_and_per_product(client, ctx):
    post_review(client, ctx["h"], ctx["p"]["id"])
    assert client.get("/api/reviews/products/999").json() == []
    assert len(client.get(f"/api/reviews/products/{ctx['p']['id']}").json()) == 1


def test_missing_product_returns_404(client, ctx):
    assert post_review(client, ctx["h"], 999).status_code == 404


@pytest.mark.parametrize(
    "body",
    [{"stars": 0, "title": "x"}, {"stars": 6, "title": "x"}, {"stars": 5, "title": ""},
     {"stars": 5, "title": "x" * 256}, {"stars": 5, "title": "x", "text": "x" * 2001}, {"title": "x"}],
)
def test_invalid_body_returns_422(client, ctx, body):
    assert client.post(f"/api/reviews/products/{ctx['p']['id']}", json=body, headers=ctx["h"]).status_code == 422


def test_create_requires_token(client, ctx):
    assert post_review(client, {}, ctx["p"]["id"]).status_code == 401


def test_service(session, ctx):
    from app.core.errors import InvalidInputError, NotFoundError
    from app.modules.reviews import service

    view = service.create_review(session, ctx["p"]["id"], ctx["uid"], 3, "Ok")
    assert view.author_name == "Ana"
    agg = service.get_aggregate(session, ctx["p"]["id"])
    assert (agg.product_id, agg.average_rating, agg.review_count) == (ctx["p"]["id"], 3.0, 1)
    assert service.get_aggregate(session, 999).average_rating == 0.0
    with pytest.raises(InvalidInputError):
        service.create_review(session, ctx["p"]["id"], ctx["uid"], 9, "x")
    with pytest.raises(InvalidInputError):
        service.create_review(session, ctx["p"]["id"], ctx["uid"], 3, "   ")
    with pytest.raises(NotFoundError):
        service.create_review(session, 999, ctx["uid"], 3, "x")


def test_unknown_author_gets_fallback_name(session, ctx):
    from app.modules.reviews import service

    assert service.create_review(session, ctx["p"]["id"], 999, 5, "Anônimo").author_name == "Usuário"


def test_review_table_is_registered():
    import app.modules.registry  # noqa: F401

    assert "review" in SQLModel.metadata.tables
