import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from tests.conftest import BUYER, BUYER_2, SELLER, create_product, login_user

CART_FIELDS = {"user_id", "items", "saved_for_later", "item_count", "total_cents"}
ITEM_FIELDS = {"product_id", "product_name", "image_url", "unit_price_cents", "quantity",
               "line_total_cents", "saved_for_later"}


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    seller_headers, _ = login_user(client, SELLER)
    buyer_headers, buyer_id = login_user(client, BUYER)
    a = create_product(client, seller_headers, name="Caneca", price_cents=3000, image_url="https://img/a.jpg")
    b = create_product(client, seller_headers, name="Chaleira", price_cents=12500)
    return {"seller": seller_headers, "h": buyer_headers, "uid": buyer_id, "a": a, "b": b}


def add(client, ctx, product_id, quantity=1):
    return client.post(f"/api/cart/{ctx['uid']}/items", json={"product_id": product_id, "quantity": quantity},
                       headers=ctx["h"])


def test_empty_cart(client, ctx):
    r = client.get(f"/api/cart/{ctx['uid']}", headers=ctx["h"])
    assert r.status_code == 200
    assert r.json() == {"user_id": ctx["uid"], "items": [], "saved_for_later": [], "item_count": 0, "total_cents": 0}


def test_add_item(client, ctx):
    r = add(client, ctx, ctx["a"]["id"], 2)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == CART_FIELDS
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == ITEM_FIELDS
    assert item == {"product_id": ctx["a"]["id"], "product_name": "Caneca", "image_url": "https://img/a.jpg",
                    "unit_price_cents": 3000, "quantity": 2, "line_total_cents": 6000, "saved_for_later": False}
    assert (body["item_count"], body["total_cents"]) == (2, 6000)


def test_add_default_quantity_is_one(client, ctx):
    r = client.post(f"/api/cart/{ctx['uid']}/items", json={"product_id": ctx["a"]["id"]}, headers=ctx["h"])
    assert r.json()["items"][0]["quantity"] == 1


def test_adding_again_sums_quantity_in_one_row(client, ctx, session):
    add(client, ctx, ctx["a"]["id"], 2)
    body = add(client, ctx, ctx["a"]["id"], 3).json()
    assert [i["quantity"] for i in body["items"]] == [5]
    assert session.execute(text("SELECT COUNT(*) FROM cart_item")).scalar() == 1


def test_totals_with_two_products_in_insertion_order(client, ctx):
    add(client, ctx, ctx["b"]["id"], 1)
    body = add(client, ctx, ctx["a"]["id"], 2).json()
    assert [i["product_id"] for i in body["items"]] == [ctx["b"]["id"], ctx["a"]["id"]]
    assert (body["item_count"], body["total_cents"]) == (3, 18500)


def test_add_missing_product_returns_404(client, ctx):
    assert add(client, ctx, 999).status_code == 404


@pytest.mark.parametrize("body", [{"product_id": 1, "quantity": 0}, {"product_id": 0}, {"quantity": 1}])
def test_add_invalid_body_returns_422(client, ctx, body):
    assert client.post(f"/api/cart/{ctx['uid']}/items", json=body, headers=ctx["h"]).status_code == 422


def test_update_quantity(client, ctx):
    add(client, ctx, ctx["a"]["id"], 2)
    r = client.put(f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}", json={"quantity": 7}, headers=ctx["h"])
    assert r.status_code == 200
    assert r.json()["items"][0]["quantity"] == 7
    assert r.json()["total_cents"] == 21000


def test_update_quantity_errors(client, ctx):
    url = f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}"
    assert client.put(url, json={"quantity": 1}, headers=ctx["h"]).status_code == 404
    add(client, ctx, ctx["a"]["id"])
    assert client.put(url, json={"quantity": 0}, headers=ctx["h"]).status_code == 422


def test_remove_item(client, ctx):
    add(client, ctx, ctx["a"]["id"])
    add(client, ctx, ctx["b"]["id"])
    r = client.delete(f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}", headers=ctx["h"])
    assert r.status_code == 200
    assert [i["product_id"] for i in r.json()["items"]] == [ctx["b"]["id"]]
    assert client.delete(f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}", headers=ctx["h"]).status_code == 404


def test_clear(client, ctx):
    add(client, ctx, ctx["a"]["id"])
    add(client, ctx, ctx["b"]["id"])
    r = client.delete(f"/api/cart/{ctx['uid']}", headers=ctx["h"])
    assert r.status_code == 200
    assert r.json()["items"] == []
    assert client.get(f"/api/cart/{ctx['uid']}", headers=ctx["h"]).json()["item_count"] == 0


def test_price_and_name_come_from_catalog(client, ctx):
    add(client, ctx, ctx["a"]["id"], 2)
    changes = {"name": "Caneca Grande", "price_cents": 4000, "stock": 5, "category": "Casa"}
    client.put(f"/api/catalog/products/{ctx['a']['id']}", json=changes, headers=ctx["seller"])
    item = client.get(f"/api/cart/{ctx['uid']}", headers=ctx["h"]).json()["items"][0]
    assert (item["product_name"], item["unit_price_cents"], item["line_total_cents"]) == ("Caneca Grande", 4000, 8000)


def test_deleted_product_disappears_from_cart(client, ctx):
    add(client, ctx, ctx["a"]["id"])
    add(client, ctx, ctx["b"]["id"])
    client.delete(f"/api/catalog/products/{ctx['a']['id']}", headers=ctx["seller"])
    body = client.get(f"/api/cart/{ctx['uid']}", headers=ctx["h"]).json()
    assert [i["product_id"] for i in body["items"]] == [ctx["b"]["id"]]
    assert body["total_cents"] == 12500


def test_carts_are_per_user(client, ctx):
    add(client, ctx, ctx["a"]["id"])
    other_headers, other_id = login_user(client, BUYER_2)
    assert client.get(f"/api/cart/{other_id}", headers=other_headers).json()["items"] == []


def test_other_users_cart_is_forbidden(client, ctx):
    other_headers, _ = login_user(client, BUYER_2)
    assert client.get(f"/api/cart/{ctx['uid']}", headers=other_headers).status_code == 403
    r = client.post(f"/api/cart/{ctx['uid']}/items", json={"product_id": ctx["a"]["id"]}, headers=other_headers)
    assert r.status_code == 403


def test_cart_requires_token(client, ctx):
    assert client.get(f"/api/cart/{ctx['uid']}").status_code == 401


def test_service_cart(session, client, ctx):
    from app.core.errors import InvalidInputError, NotFoundError
    from app.modules.cart import service

    view = service.add_item(session, ctx["uid"], ctx["a"]["id"], 1)
    assert view.items[0].product_name == "Caneca"
    with pytest.raises(InvalidInputError):
        service.add_item(session, ctx["uid"], ctx["a"]["id"], 0)
    with pytest.raises(NotFoundError):
        service.remove_item(session, ctx["uid"], ctx["b"]["id"])
    assert service.clear(session, ctx["uid"]).items == []


def test_cart_table_is_registered():
    import app.modules.registry  # noqa: F401

    assert "cart_item" in SQLModel.metadata.tables
