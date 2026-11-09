import pytest
from sqlalchemy import text

from tests.conftest import SELLER, SELLER_2, create_product, login_user


@pytest.fixture(name="seller")
def seller_fixture(client):
    return login_user(client, SELLER)


def make_many(client, headers, n, **overrides):
    return [create_product(client, headers, name=f"Produto {i}", **overrides) for i in range(n)]


# ---------- GET /products ----------


def test_list_is_paginated_and_ordered_by_id(client, seller):
    created = make_many(client, seller[0], 5)
    r = client.get("/api/catalog/products", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"items", "total", "page", "page_size"}
    assert body["total"] == 5
    assert (body["page"], body["page_size"]) == (1, 2)
    assert [p["id"] for p in body["items"]] == [created[0]["id"], created[1]["id"]]
    page3 = client.get("/api/catalog/products", params={"page": 3, "page_size": 2}).json()
    assert [p["id"] for p in page3["items"]] == [created[4]["id"]]


def test_list_defaults(client, seller):
    make_many(client, seller[0], 3)
    body = client.get("/api/catalog/products").json()
    assert (body["page"], body["page_size"], body["total"]) == (1, 20, 3)


def test_page_beyond_end_is_empty(client, seller):
    make_many(client, seller[0], 2)
    body = client.get("/api/catalog/products", params={"page": 5}).json()
    assert body["items"] == []
    assert body["total"] == 2


def test_list_filters_by_category(client, seller):
    make_many(client, seller[0], 2, category="Livros")
    make_many(client, seller[0], 3, category="Brinquedos")
    body = client.get("/api/catalog/products", params={"category": "Livros"}).json()
    assert body["total"] == 2
    assert {p["category"] for p in body["items"]} == {"Livros"}


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}, {"page": "x"}])
def test_invalid_pagination_returns_422(client, params):
    assert client.get("/api/catalog/products", params=params).status_code == 422


def test_empty_catalog(client):
    assert client.get("/api/catalog/products").json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


# ---------- GET /categories ----------


def test_categories_are_distinct_and_sorted(client, seller):
    for category in ["Livros", "Brinquedos", "Livros", "Casa"]:
        create_product(client, seller[0], category=category)
    r = client.get("/api/catalog/categories")
    assert r.status_code == 200
    assert r.json() == ["Brinquedos", "Casa", "Livros"]


def test_categories_empty(client):
    assert client.get("/api/catalog/categories").json() == []


# ---------- service ----------


def test_core_pagination_page_model():
    from app.core.pagination import Page

    page = Page[int](items=[1, 2], total=10, page=1, page_size=2)
    assert page.model_dump() == {"items": [1, 2], "total": 10, "page": 1, "page_size": 2}


def test_service_list_products_and_errors(client, session, seller):
    from app.core.errors import InvalidInputError
    from app.modules.catalog import service

    make_many(client, seller[0], 3)
    items, total = service.list_products(session, page=2, page_size=2)
    assert total == 3
    assert len(items) == 1
    with pytest.raises(InvalidInputError):
        service.list_products(session, page=0)


def test_service_list_by_seller(client, session, seller):
    from app.modules.catalog import service

    make_many(client, seller[0], 3)
    other_headers, other_id = login_user(client, SELLER_2)
    create_product(client, other_headers)
    items, total = service.list_by_seller(session, other_id)
    assert total == 1
    assert items[0].seller_id == other_id
    items, total = service.list_by_seller(session, seller[1], page=1, page_size=2)
    assert (len(items), total) == (2, 3)


def test_service_get_many_ignores_unknown_ids(client, session, seller):
    from app.modules.catalog import service

    a, b = make_many(client, seller[0], 2)
    found = service.get_many(session, [b["id"], 999, a["id"]])
    assert sorted(p.id for p in found) == [a["id"], b["id"]]
    assert service.get_many(session, []) == []


def test_service_filter_products(client, session, seller):
    from app.modules.catalog import service

    cheap = create_product(client, seller[0], price_cents=1000, category="Livros")
    mid = create_product(client, seller[0], price_cents=5000, category="Livros")
    pricey = create_product(client, seller[0], price_cents=9000, category="Casa")
    session.execute(text("UPDATE product SET average_rating = 4.5 WHERE id = :id"), {"id": mid["id"]})
    session.commit()

    def ids(**kwargs):
        return [p.id for p in service.filter_products(session, **kwargs)]

    assert ids() == [cheap["id"], mid["id"], pricey["id"]]
    assert ids(category="Livros") == [cheap["id"], mid["id"]]
    assert ids(min_price_cents=5000) == [mid["id"], pricey["id"]]  # inclusivo
    assert ids(max_price_cents=5000) == [cheap["id"], mid["id"]]  # inclusivo
    assert ids(min_rating=4.0) == [mid["id"]]
    assert ids(category="Casa", max_price_cents=5000) == []
