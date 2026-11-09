import dataclasses
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from tests.conftest import ADDRESS, BUYER, BUYER_2, SELLER, SELLER_2, checkout, create_product, login_user

ORDER_FIELDS = {
    "id", "buyer_id", "status", "fulfillment_status", "total_cents", "address", "shipping_method",
    "payment_method", "items", "created_at", "paid_at", "shipped_at", "out_for_delivery_at", "delivered_at",
    "estimated_delivery_date",
}


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    seller_headers, seller_id = login_user(client, SELLER)
    buyer_headers, buyer_id = login_user(client, BUYER)
    a = create_product(client, seller_headers, name="Caneca", price_cents=3000, stock=5)
    b = create_product(client, seller_headers, name="Chaleira", price_cents=12500, stock=2)
    return {"seller": seller_headers, "seller_id": seller_id, "h": buyer_headers, "uid": buyer_id, "a": a, "b": b}


def stock(client, product_id):
    return client.get(f"/api/catalog/products/{product_id}").json()["stock"]


def order_count(session):
    return session.execute(text('SELECT COUNT(*) FROM "order"')).scalar()


def use_gateway(mode):
    from app.modules.payments import service as payments

    payments.set_gateway(payments.MockPaymentGateway(mode))


# ---------- sucesso ----------


def test_checkout_success(client, ctx):
    r = checkout(client, ctx["h"], [(ctx["a"]["id"], 2), (ctx["b"]["id"], 1)])
    assert r.status_code == 200, r.text
    order = r.json()
    assert set(order) == ORDER_FIELDS
    assert order["status"] == "PAID"
    assert order["fulfillment_status"] == "NOT_SHIPPED"
    assert order["buyer_id"] == ctx["uid"]
    assert order["total_cents"] == 2 * 3000 + 12500
    assert order["address"] == ADDRESS
    assert (order["shipping_method"], order["payment_method"]) == ("STANDARD", "CARD")
    assert order["paid_at"] is not None
    assert order["shipped_at"] is None
    assert order["estimated_delivery_date"] is not None
    items = {i["product_id"]: i for i in order["items"]}
    assert items[ctx["a"]["id"]]["quantity"] == 2
    assert items[ctx["a"]["id"]]["unit_price_cents"] == 3000
    assert items[ctx["a"]["id"]]["seller_id"] == ctx["seller_id"]
    assert set(items[ctx["a"]["id"]]) == {"id", "product_id", "seller_id", "quantity", "unit_price_cents"}


def test_checkout_decreases_stock(client, ctx):
    checkout(client, ctx["h"], [(ctx["a"]["id"], 2), (ctx["b"]["id"], 2)])
    assert stock(client, ctx["a"]["id"]) == 3
    assert stock(client, ctx["b"]["id"]) == 0


def test_repeated_product_becomes_one_item(client, ctx):
    order = checkout(client, ctx["h"], [(ctx["a"]["id"], 1), (ctx["a"]["id"], 2)]).json()
    assert [(i["product_id"], i["quantity"]) for i in order["items"]] == [(ctx["a"]["id"], 3)]
    assert order["total_cents"] == 9000


def test_items_from_two_sellers_keep_their_seller(client, ctx):
    other, other_id = login_user(client, SELLER_2)
    c = create_product(client, other, name="Livro", price_cents=5000)
    order = checkout(client, ctx["h"], [(ctx["a"]["id"], 1), (c["id"], 1)]).json()
    assert {i["product_id"]: i["seller_id"] for i in order["items"]} == {
        ctx["a"]["id"]: ctx["seller_id"], c["id"]: other_id}


def test_unit_price_is_a_snapshot(client, ctx, session):
    order = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    changes = {"name": "Caneca", "price_cents": 9999, "stock": 10, "category": "Casa"}
    client.put(f"/api/catalog/products/{ctx['a']['id']}", json=changes, headers=ctx["seller"])
    price = session.execute(text("SELECT unit_price_cents FROM order_item WHERE order_id = :id"),
                            {"id": order["id"]}).scalar()
    assert price == 3000


def test_express_and_pickup_are_accepted(client, ctx):
    r = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], shipping_method="EXPRESS", payment_method="GIFT")
    assert (r.json()["shipping_method"], r.json()["payment_method"]) == ("EXPRESS", "GIFT")
    assert checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], shipping_method="PICKUP").status_code == 200


# ---------- erros ----------


def test_seller_cannot_checkout(client, ctx):
    assert checkout(client, ctx["seller"], [(ctx["a"]["id"], 1)]).status_code == 403


def test_checkout_requires_token(client, ctx):
    assert checkout(client, {}, [(ctx["a"]["id"], 1)]).status_code == 401


@pytest.mark.parametrize(
    "overrides",
    [
        {"items": []},
        {"items": [{"product_id": 1, "quantity": 0}]},
        {"address": {**ADDRESS, "city": ""}},
        {"address": {**ADDRESS, "zip": "   "}},
        {"address": {k: v for k, v in ADDRESS.items() if k != "street"}},
        {"shipping_method": "DRONE"},
        {"payment_method": "PIX"},
    ],
)
def test_invalid_body_returns_422(client, ctx, overrides):
    assert checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], **overrides).status_code == 422


def test_missing_product_returns_404_and_touches_nothing(client, ctx, session):
    r = checkout(client, ctx["h"], [(ctx["a"]["id"], 1), (999, 1)])
    assert r.status_code == 404
    assert stock(client, ctx["a"]["id"]) == 5
    assert order_count(session) == 0


def test_insufficient_stock_returns_409_and_restores_everything(client, ctx, session):
    r = checkout(client, ctx["h"], [(ctx["a"]["id"], 2), (ctx["b"]["id"], 3)])
    assert r.status_code == 409
    assert stock(client, ctx["a"]["id"]) == 5
    assert stock(client, ctx["b"]["id"]) == 2
    assert order_count(session) == 0


# ---------- pagamento recusado ----------


def test_declined_payment_returns_failed_order_and_restores_stock(client, ctx):
    use_gateway("always")
    r = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)])
    assert r.status_code == 200
    assert r.json()["status"] == "FAILED"
    assert r.json()["paid_at"] is None
    assert stock(client, ctx["a"]["id"]) == 5


class ExplodingGateway:
    def charge(self, order_id, amount_cents, currency):
        raise RuntimeError("gateway fora do ar")


def test_gateway_exception_marks_failed_restores_stock_and_propagates(session, ctx):
    from app.modules.catalog import service as catalog
    from app.modules.orders import service
    from app.modules.payments import service as payments

    payments.set_gateway(ExplodingGateway())
    with pytest.raises(RuntimeError):
        service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 2)],
                         service.Address(**ADDRESS), service.ShippingMethod.STANDARD, service.PaymentMethod.CARD)
    session.expire_all()
    assert catalog.get_product(session, ctx["a"]["id"]).stock == 5
    status = session.execute(text('SELECT status FROM "order"')).scalar()
    assert status == "FAILED"


def test_order_is_created_before_charge_with_its_id(session, ctx):
    from app.modules.orders import service
    from app.modules.payments import service as payments

    seen = []

    class Spy:
        def charge(self, order_id, amount_cents, currency):
            seen.append((order_id, amount_cents, currency))
            return payments.PaymentResult(True, "spy_1", "ok")

    payments.set_gateway(Spy())
    order = service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 1)],
                             service.Address(**ADDRESS), service.ShippingMethod.STANDARD,
                             service.PaymentMethod.CARD)
    assert seen == [(order.id, 3000, "BRL")]


# ---------- idempotência ----------


def test_same_idempotency_key_returns_same_order(client, ctx, session):
    first = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)], key="abc-123").json()
    second = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)], key="abc-123").json()
    assert first["id"] == second["id"]
    assert stock(client, ctx["a"]["id"]) == 3
    assert order_count(session) == 1


def test_different_keys_create_different_orders(client, ctx):
    a = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], key="k1").json()
    b = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], key="k2").json()
    assert a["id"] != b["id"]


def test_no_key_creates_new_order_each_time(client, ctx, session):
    checkout(client, ctx["h"], [(ctx["a"]["id"], 1)])
    checkout(client, ctx["h"], [(ctx["a"]["id"], 1)])
    assert order_count(session) == 2


def test_idempotency_key_is_per_buyer(client, ctx):
    other, _ = login_user(client, BUYER_2)
    a = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)], key="mesma").json()
    b = checkout(client, other, [(ctx["a"]["id"], 1)], key="mesma").json()
    assert a["id"] != b["id"]
    assert b["buyer_id"] != a["buyer_id"]


# ---------- estrutura e entrega ----------


def test_tables_are_registered():
    import app.modules.registry  # noqa: F401

    assert {"order", "order_item"} <= set(SQLModel.metadata.tables)


def test_service_view_is_frozen_dataclass(session, ctx):
    from app.modules.orders import service

    order = service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 1)],
                             service.Address(**ADDRESS), service.ShippingMethod.STANDARD,
                             service.PaymentMethod.CARD)
    assert dataclasses.is_dataclass(order)
    assert isinstance(order.address, service.Address)
    assert order.status == service.OrderStatus.PAID
    with pytest.raises(dataclasses.FrozenInstanceError):
        order.status = service.OrderStatus.FAILED


def test_service_rejects_empty_and_blank(session, ctx):
    from app.core.errors import InvalidInputError
    from app.modules.orders import service

    address = service.Address(**ADDRESS)
    with pytest.raises(InvalidInputError):
        service.checkout(session, ctx["uid"], [], address, service.ShippingMethod.STANDARD, service.PaymentMethod.CARD)
    with pytest.raises(InvalidInputError):
        service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 1)],
                         dataclasses.replace(address, city=" "), service.ShippingMethod.STANDARD,
                         service.PaymentMethod.CARD)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "start, method, expected",
    [
        (utc(2024, 1, 5, 15), "STANDARD", date(2024, 1, 12)),  # sexta + 5 dias úteis
        (utc(2024, 1, 5, 15), "EXPRESS", date(2024, 1, 8)),  # sexta + 1 → segunda
        (utc(2024, 1, 5, 15), "PICKUP", date(2024, 1, 12)),
        (utc(2024, 1, 6, 15), "EXPRESS", date(2024, 1, 8)),  # sábado → segunda
        (utc(2024, 1, 5, 2), "EXPRESS", date(2024, 1, 5)),  # 02:00 UTC ainda é quinta em São Paulo
    ],
)
def test_delivery_estimate(start, method, expected):
    from app.modules.orders import delivery
    from app.modules.orders.models import ShippingMethod

    assert delivery.estimate(start, ShippingMethod(method)) == expected


def test_delivery_estimate_none():
    from app.modules.orders import delivery
    from app.modules.orders.models import ShippingMethod

    assert delivery.estimate(None, ShippingMethod.STANDARD) is None
