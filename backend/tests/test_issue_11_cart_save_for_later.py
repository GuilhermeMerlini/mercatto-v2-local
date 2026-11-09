import pytest

from tests.conftest import BUYER, BUYER_2, SELLER, create_product, login_user


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    seller_headers, _ = login_user(client, SELLER)
    headers, uid = login_user(client, BUYER)
    a = create_product(client, seller_headers, name="Caneca", price_cents=3000)
    b = create_product(client, seller_headers, name="Chaleira", price_cents=12500)
    for product, qty in ((a, 2), (b, 1)):
        client.post(f"/api/cart/{uid}/items", json={"product_id": product["id"], "quantity": qty}, headers=headers)
    return {"h": headers, "uid": uid, "a": a, "b": b}


def act(client, ctx, product_id, action):
    return client.post(f"/api/cart/{ctx['uid']}/items/{product_id}/{action}", headers=ctx["h"])


def test_save_for_later_moves_item_out_of_totals(client, ctx):
    r = act(client, ctx, ctx["a"]["id"], "save-for-later")
    assert r.status_code == 200
    body = r.json()
    assert [i["product_id"] for i in body["items"]] == [ctx["b"]["id"]]
    assert [i["product_id"] for i in body["saved_for_later"]] == [ctx["a"]["id"]]
    saved = body["saved_for_later"][0]
    assert (saved["quantity"], saved["saved_for_later"]) == (2, True)
    assert (body["item_count"], body["total_cents"]) == (1, 12500)


def test_move_back_to_cart(client, ctx):
    act(client, ctx, ctx["a"]["id"], "save-for-later")
    r = act(client, ctx, ctx["a"]["id"], "move-to-cart")
    assert r.status_code == 200
    body = r.json()
    assert body["saved_for_later"] == []
    assert sorted(i["product_id"] for i in body["items"]) == sorted([ctx["a"]["id"], ctx["b"]["id"]])
    assert (body["item_count"], body["total_cents"]) == (3, 18500)


def test_actions_are_idempotent(client, ctx):
    act(client, ctx, ctx["a"]["id"], "save-for-later")
    assert act(client, ctx, ctx["a"]["id"], "save-for-later").status_code == 200
    assert act(client, ctx, ctx["b"]["id"], "move-to-cart").status_code == 200


def test_missing_item_returns_404(client, ctx):
    assert act(client, ctx, 999, "save-for-later").status_code == 404
    assert act(client, ctx, 999, "move-to-cart").status_code == 404


def test_adding_a_saved_item_moves_it_back_and_sums(client, ctx):
    act(client, ctx, ctx["a"]["id"], "save-for-later")
    r = client.post(f"/api/cart/{ctx['uid']}/items", json={"product_id": ctx["a"]["id"], "quantity": 1},
                    headers=ctx["h"])
    body = r.json()
    assert body["saved_for_later"] == []
    assert {i["product_id"]: i["quantity"] for i in body["items"]}[ctx["a"]["id"]] == 3


def test_saved_item_can_be_removed(client, ctx):
    act(client, ctx, ctx["a"]["id"], "save-for-later")
    r = client.delete(f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}", headers=ctx["h"])
    assert r.json()["saved_for_later"] == []


def test_only_owner(client, ctx):
    other, _ = login_user(client, BUYER_2)
    url = f"/api/cart/{ctx['uid']}/items/{ctx['a']['id']}/save-for-later"
    assert client.post(url, headers=other).status_code == 403
    assert client.post(url).status_code == 401


def test_service_functions(session, ctx):
    from app.core.errors import NotFoundError
    from app.modules.cart import service

    view = service.save_for_later(session, ctx["uid"], ctx["b"]["id"])
    assert [i.product_id for i in view.saved_for_later] == [ctx["b"]["id"]]
    view = service.move_to_cart(session, ctx["uid"], ctx["b"]["id"])
    assert view.saved_for_later == []
    with pytest.raises(NotFoundError):
        service.save_for_later(session, ctx["uid"], 999)
