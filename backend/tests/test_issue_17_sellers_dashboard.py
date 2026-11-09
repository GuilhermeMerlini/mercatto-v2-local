import pytest

from tests.conftest import BUYER, SELLER, SELLER_2, checkout, create_product, login_user


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    s1, s1_id = login_user(client, SELLER)
    s2, s2_id = login_user(client, SELLER_2)
    buyer, buyer_id = login_user(client, BUYER)
    a = create_product(client, s1, name="Caneca", price_cents=3000, stock=20)
    b = create_product(client, s1, name="Prato", price_cents=2000, stock=4)
    c = create_product(client, s2, name="Livro", price_cents=5000, stock=20)
    order = checkout(client, buyer, [(a["id"], 2), (c["id"], 1)]).json()
    return {"s1": s1, "s1_id": s1_id, "s2": s2, "s2_id": s2_id, "buyer": buyer, "buyer_id": buyer_id,
            "a": a, "b": b, "c": c, "order": order}


def use_gateway(mode):
    from app.modules.payments import service as payments

    payments.set_gateway(payments.MockPaymentGateway(mode))


def advance(client, ctx, status, order_id=None, seller="s1"):
    seller_id = ctx[f"{seller}_id"]
    return client.post(f"/api/sellers/{seller_id}/orders/{order_id or ctx['order']['id']}/fulfillment",
                       json={"status": status}, headers=ctx[seller])


# ---------- pedidos recebidos ----------


def test_received_orders_show_only_my_items(client, ctx):
    r = client.get(f"/api/sellers/{ctx['s1_id']}/orders", headers=ctx["s1"])
    assert r.status_code == 200
    [order] = r.json()
    assert set(order) == {"id", "buyer_id", "status", "fulfillment_status", "created_at", "items", "subtotal_cents"}
    assert order["id"] == ctx["order"]["id"]
    assert order["buyer_id"] == ctx["buyer_id"]
    assert order["status"] == "PAID"
    assert order["fulfillment_status"] == "NOT_SHIPPED"
    assert order["items"] == [{"product_id": ctx["a"]["id"], "quantity": 2, "unit_price_cents": 3000}]
    assert order["subtotal_cents"] == 6000
    other = client.get(f"/api/sellers/{ctx['s2_id']}/orders", headers=ctx["s2"]).json()
    assert other[0]["subtotal_cents"] == 5000


def test_orders_service_list_by_seller_keeps_all_items(session, ctx):
    from app.modules.orders import service

    [order] = service.list_by_seller(session, ctx["s1_id"])
    assert len(order.items) == 2
    assert service.list_by_seller(session, 999) == []


# ---------- inventário e métricas ----------


def test_inventory(client, ctx):
    r = client.get(f"/api/sellers/{ctx['s1_id']}/products", params={"page_size": 1}, headers=ctx["s1"])
    assert r.status_code == 200
    body = r.json()
    assert (body["total"], body["page"], body["page_size"]) == (2, 1, 1)
    assert body["items"][0]["id"] == ctx["a"]["id"]


def test_metrics(client, ctx):
    use_gateway("always")
    checkout(client, ctx["buyer"], [(ctx["a"]["id"], 5)])  # recusado: não entra na receita
    r = client.get(f"/api/sellers/{ctx['s1_id']}/metrics", headers=ctx["s1"])
    assert r.status_code == 200
    body = r.json()
    assert body["total_revenue_cents"] == 6000
    assert [p["id"] for p in body["low_stock_products"]] == [ctx["b"]["id"]]


# ---------- acesso ----------


@pytest.mark.parametrize("path", ["orders", "products", "metrics"])
def test_only_the_seller_itself(client, ctx, path):
    url = f"/api/sellers/{ctx['s1_id']}/{path}"
    assert client.get(url, headers=ctx["s2"]).status_code == 403
    assert client.get(url, headers=ctx["buyer"]).status_code == 403
    assert client.get(url).status_code == 401


def test_buyer_cannot_open_own_id_as_seller(client, ctx):
    assert client.get(f"/api/sellers/{ctx['buyer_id']}/orders", headers=ctx["buyer"]).status_code == 403


# ---------- envio ----------


def test_fulfillment_happy_path(client, ctx):
    for status in ("SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"):
        r = advance(client, ctx, status)
        assert r.status_code == 200, r.text
        assert r.json()["fulfillment_status"] == status
    order = client.get(f"/api/orders/{ctx['order']['id']}", headers=ctx["buyer"]).json()
    assert order["fulfillment_status"] == "DELIVERED"
    assert order["shipped_at"] and order["out_for_delivery_at"] and order["delivered_at"]


def test_cannot_skip_or_go_back(client, ctx):
    assert advance(client, ctx, "DELIVERED").status_code == 409
    advance(client, ctx, "SHIPPED")
    assert advance(client, ctx, "SHIPPED").status_code == 409


def test_unpaid_order_cannot_ship(client, ctx):
    use_gateway("always")
    failed = checkout(client, ctx["buyer"], [(ctx["a"]["id"], 1)]).json()
    assert advance(client, ctx, "SHIPPED", order_id=failed["id"]).status_code == 409


def test_seller_without_items_in_order_is_forbidden(client, ctx):
    order = checkout(client, ctx["buyer"], [(ctx["a"]["id"], 1)]).json()
    assert advance(client, ctx, "SHIPPED", order_id=order["id"], seller="s2").status_code == 403


def test_fulfillment_errors(client, ctx):
    assert advance(client, ctx, "SHIPPED", order_id=999).status_code == 404
    assert advance(client, ctx, "NOT_SHIPPED").status_code == 422
    assert advance(client, ctx, "TELEPORTED").status_code == 422


def test_shipping_locks_address(client, ctx):
    advance(client, ctx, "SHIPPED")
    r = client.patch(f"/api/orders/{ctx['order']['id']}/address",
                     json={"full_name": "X", "street": "Y", "city": "Z", "state": "W", "zip": "1"},
                     headers=ctx["buyer"])
    assert r.status_code == 409


def test_services(session, ctx):
    from app.core.errors import ConflictError, ForbiddenError, InvalidInputError
    from app.modules.orders import service as orders
    from app.modules.sellers import service as sellers

    with pytest.raises(ForbiddenError):
        orders.advance_fulfillment(session, ctx["order"]["id"], 999, orders.FulfillmentStatus.SHIPPED)
    with pytest.raises(ConflictError):
        orders.advance_fulfillment(session, ctx["order"]["id"], ctx["s1_id"], orders.FulfillmentStatus.DELIVERED)
    with pytest.raises(InvalidInputError):
        sellers.advance_fulfillment(session, ctx["s1_id"], ctx["order"]["id"], "VOANDO")
    view = sellers.advance_fulfillment(session, ctx["s1_id"], ctx["order"]["id"], "SHIPPED")
    assert view.fulfillment_status == "SHIPPED"
    metrics = sellers.get_metrics(session, ctx["s1_id"])
    assert metrics.total_revenue_cents == 6000
