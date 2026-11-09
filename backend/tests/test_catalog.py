import pytest

from app.core.errors import InsufficientStockError, NotFoundError
from app.modules.catalog import service as catalog_service
from tests.conftest import make_auth_headers


def make_category(client, headers, name="Eletrônicos"):
    r = client.post("/catalog/categories", json={"name": name}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def make_product(client, headers, category_id, **overrides):
    body = {
        "name": "Fone Bluetooth",
        "description": "Fone sem fio",
        "price_cents": 19990,
        "stock": 10,
        "category_id": category_id,
        **overrides,
    }
    r = client.post("/catalog/products", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- categories ----------


def test_create_and_list_categories(client, auth_headers):
    created = make_category(client, auth_headers, "Livros")
    assert isinstance(created["id"], int) and created["name"] == "Livros"
    r = client.get("/catalog/categories")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()] == ["Livros"]


def test_create_category_requires_auth(client):
    assert client.post("/catalog/categories", json={"name": "X"}).status_code == 401


# ---------- create product ----------


def test_create_product_returns_201_with_all_fields(client, auth_headers):
    cat = make_category(client, auth_headers)
    me = client.get("/users/me", headers=auth_headers).json()
    p = make_product(client, auth_headers, cat["id"])
    assert isinstance(p["id"], int)
    assert p["name"] == "Fone Bluetooth"
    assert p["description"] == "Fone sem fio"
    assert p["price_cents"] == 19990
    assert p["stock"] == 10
    assert p["category_id"] == cat["id"]
    assert p["seller_id"] == me["id"]


def test_create_product_requires_auth(client, auth_headers):
    cat = make_category(client, auth_headers)
    body = {"name": "X", "description": "", "price_cents": 100, "stock": 1, "category_id": cat["id"]}
    assert client.post("/catalog/products", json=body).status_code == 401


def test_create_product_negative_price_returns_422(client, auth_headers):
    cat = make_category(client, auth_headers)
    body = {"name": "X", "description": "", "price_cents": -1, "stock": 1, "category_id": cat["id"]}
    assert client.post("/catalog/products", json=body, headers=auth_headers).status_code == 422


def test_create_product_negative_stock_returns_422(client, auth_headers):
    cat = make_category(client, auth_headers)
    body = {"name": "X", "description": "", "price_cents": 100, "stock": -5, "category_id": cat["id"]}
    assert client.post("/catalog/products", json=body, headers=auth_headers).status_code == 422


def test_create_product_unknown_category_returns_404(client, auth_headers):
    body = {"name": "X", "description": "", "price_cents": 100, "stock": 1, "category_id": 9999}
    assert client.post("/catalog/products", json=body, headers=auth_headers).status_code == 404


def test_seller_id_comes_from_token(client):
    h1 = make_auth_headers(client, {"email": "a@example.com", "password": "senha-123", "name": "A"})
    h2 = make_auth_headers(client, {"email": "b@example.com", "password": "senha-123", "name": "B"})
    cat = make_category(client, h1)
    p = make_product(client, h2, cat["id"])
    assert p["seller_id"] == client.get("/users/me", headers=h2).json()["id"]


# ---------- get product ----------


def test_get_product_by_id(client, auth_headers):
    cat = make_category(client, auth_headers)
    p = make_product(client, auth_headers, cat["id"])
    r = client.get(f"/catalog/products/{p['id']}")
    assert r.status_code == 200
    assert r.json() == p


def test_get_product_not_found_returns_404(client):
    assert client.get("/catalog/products/9999").status_code == 404


# ---------- list products ----------


def test_list_products_has_pagination_shape(client, auth_headers):
    cat = make_category(client, auth_headers)
    for i in range(3):
        make_product(client, auth_headers, cat["id"], name=f"P{i}")
    r = client.get("/catalog/products")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"items", "total", "page", "page_size"}
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_list_products_pagination(client, auth_headers):
    cat = make_category(client, auth_headers)
    for i in range(5):
        make_product(client, auth_headers, cat["id"], name=f"P{i}")
    p1 = client.get("/catalog/products?page=1&page_size=2").json()
    p3 = client.get("/catalog/products?page=3&page_size=2").json()
    assert p1["total"] == 5 and len(p1["items"]) == 2
    assert p3["total"] == 5 and len(p3["items"]) == 1
    ids = {i["id"] for i in p1["items"]} | {i["id"] for i in p3["items"]}
    assert len(ids) == 3  # páginas diferentes não repetem produtos


def test_list_products_filter_by_category(client, auth_headers):
    c1 = make_category(client, auth_headers, "A")
    c2 = make_category(client, auth_headers, "B")
    make_product(client, auth_headers, c1["id"], name="em A")
    make_product(client, auth_headers, c2["id"], name="em B 1")
    make_product(client, auth_headers, c2["id"], name="em B 2")
    body = client.get(f"/catalog/products?category_id={c2['id']}").json()
    assert body["total"] == 2
    assert {i["name"] for i in body["items"]} == {"em B 1", "em B 2"}


def test_list_products_empty(client):
    body = client.get("/catalog/products").json()
    assert body["items"] == [] and body["total"] == 0


def test_list_products_invalid_page_returns_422(client):
    assert client.get("/catalog/products?page=0").status_code == 422
    assert client.get("/catalog/products?page_size=0").status_code == 422


# ---------- service: get_product / decrease_stock ----------


def test_service_get_product(client, session, auth_headers):
    cat = make_category(client, auth_headers)
    p = make_product(client, auth_headers, cat["id"])
    assert catalog_service.get_product(session, p["id"]).id == p["id"]


def test_service_get_product_not_found_raises(session):
    with pytest.raises(NotFoundError):
        catalog_service.get_product(session, 9999)


def test_decrease_stock_reduces_and_persists(client, session, auth_headers):
    cat = make_category(client, auth_headers)
    p = make_product(client, auth_headers, cat["id"], stock=5)
    catalog_service.decrease_stock(session, p["id"], 2)
    assert client.get(f"/catalog/products/{p['id']}").json()["stock"] == 3


def test_decrease_stock_to_exactly_zero_is_allowed(client, session, auth_headers):
    cat = make_category(client, auth_headers)
    p = make_product(client, auth_headers, cat["id"], stock=2)
    catalog_service.decrease_stock(session, p["id"], 2)
    assert client.get(f"/catalog/products/{p['id']}").json()["stock"] == 0


def test_decrease_stock_insufficient_raises_and_keeps_stock(client, session, auth_headers):
    cat = make_category(client, auth_headers)
    p = make_product(client, auth_headers, cat["id"], stock=2)
    with pytest.raises(InsufficientStockError):
        catalog_service.decrease_stock(session, p["id"], 3)
    assert client.get(f"/catalog/products/{p['id']}").json()["stock"] == 2


def test_decrease_stock_unknown_product_raises(session):
    with pytest.raises(NotFoundError):
        catalog_service.decrease_stock(session, 9999, 1)
