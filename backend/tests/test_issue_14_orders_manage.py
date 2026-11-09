import pytest
from sqlalchemy import text

from tests.conftest import ADDRESS, BUYER, BUYER_2, SELLER, checkout, create_product, login_user

NEW_ADDRESS = {"full_name": "Ana S.", "street": "Av. Ipiranga, 50", "city": "Canoas", "state": "RS", "zip": "92000-000"}


@pytest.fixture(name="ctx")
def ctx_fixture(client):
    seller_headers, _ = login_user(client, SELLER)
    buyer_headers, buyer_id = login_user(client, BUYER)
    a = create_product(client, seller_headers, name="Caneca", price_cents=3000, stock=5)
    return {"seller": seller_headers, "h": buyer_headers, "uid": buyer_id, "a": a}


def use_gateway(mode):
    from app.modules.payments import service as payments

    payments.set_gateway(payments.MockPaymentGateway(mode))


def stock(client, product_id):
    return client.get(f"/api/catalog/products/{product_id}").json()["stock"]


def set_order(session, order_id, **values):
    assignments = ", ".join(f"{k} = :{k}" for k in values)
    session.execute(text(f'UPDATE "order" SET {assignments} WHERE id = :id'), {**values, "id": order_id})
    session.commit()


# ---------- leitura ----------


def test_list_my_orders_newest_first(client, ctx):
    first = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    second = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    r = client.get("/api/orders", headers=ctx["h"])
    assert r.status_code == 200
    assert [o["id"] for o in r.json()] == [second["id"], first["id"]]
    assert r.json()[0]["items"][0]["product_id"] == ctx["a"]["id"]


def test_list_only_shows_own_orders(client, ctx):
    checkout(client, ctx["h"], [(ctx["a"]["id"], 1)])
    other, _ = login_user(client, BUYER_2)
    assert client.get("/api/orders", headers=other).json() == []


def test_get_order(client, ctx):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)]).json()
    r = client.get(f"/api/orders/{created['id']}", headers=ctx["h"])
    assert r.status_code == 200
    assert r.json() == created


def test_get_order_errors(client, ctx):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    other, _ = login_user(client, BUYER_2)
    assert client.get(f"/api/orders/{created['id']}", headers=other).status_code == 403
    assert client.get("/api/orders/999", headers=ctx["h"]).status_code == 404
    assert client.get(f"/api/orders/{created['id']}").status_code == 401
    assert client.get("/api/orders").status_code == 401


# ---------- endereço ----------


def test_update_address(client, ctx):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    r = client.patch(f"/api/orders/{created['id']}/address", json=NEW_ADDRESS, headers=ctx["h"])
    assert r.status_code == 200
    assert r.json()["address"] == NEW_ADDRESS
    assert client.get(f"/api/orders/{created['id']}", headers=ctx["h"]).json()["address"] == NEW_ADDRESS


def test_update_address_validation_and_access(client, ctx):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    url = f"/api/orders/{created['id']}/address"
    assert client.patch(url, json={**NEW_ADDRESS, "street": " "}, headers=ctx["h"]).status_code == 422
    other, _ = login_user(client, BUYER_2)
    assert client.patch(url, json=NEW_ADDRESS, headers=other).status_code == 403
    assert client.patch("/api/orders/999/address", json=NEW_ADDRESS, headers=ctx["h"]).status_code == 404


@pytest.mark.parametrize("fulfillment", ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"])
def test_address_locked_after_shipping(client, ctx, session, fulfillment):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    set_order(session, created["id"], fulfillment_status=fulfillment)
    r = client.patch(f"/api/orders/{created['id']}/address", json=NEW_ADDRESS, headers=ctx["h"])
    assert r.status_code == 409
    assert client.get(f"/api/orders/{created['id']}", headers=ctx["h"]).json()["address"] == ADDRESS


def test_address_locked_when_cancelled(client, ctx, session):
    created = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    set_order(session, created["id"], status="CANCELLED")
    assert client.patch(f"/api/orders/{created['id']}/address", json=NEW_ADDRESS, headers=ctx["h"]).status_code == 409


# ---------- nova tentativa de pagamento ----------


def retry(client, ctx, order_id, method="STORE", headers=None):
    return client.post(f"/api/orders/{order_id}/payment", json={"payment_method": method},
                       headers=headers or ctx["h"])


def test_retry_after_decline_pays_and_takes_stock_once(client, ctx):
    use_gateway("first-attempt")
    failed = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)]).json()
    assert failed["status"] == "FAILED"
    assert stock(client, ctx["a"]["id"]) == 5
    r = retry(client, ctx, failed["id"], "STORE")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == failed["id"]
    assert body["status"] == "PAID"
    assert body["payment_method"] == "STORE"
    assert body["paid_at"] is not None
    assert stock(client, ctx["a"]["id"]) == 3


def test_retry_declined_again_stays_failed_and_restores_stock(client, ctx):
    use_gateway("always")
    failed = checkout(client, ctx["h"], [(ctx["a"]["id"], 2)]).json()
    body = retry(client, ctx, failed["id"]).json()
    assert body["status"] == "FAILED"
    assert stock(client, ctx["a"]["id"]) == 5


def test_retry_only_for_failed_orders(client, ctx):
    paid = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    assert retry(client, ctx, paid["id"]).status_code == 409


def test_retry_without_stock_returns_409_and_stays_failed(client, ctx, session):
    use_gateway("always")
    failed = checkout(client, ctx["h"], [(ctx["a"]["id"], 4)]).json()
    use_gateway("none")
    checkout(client, ctx["h"], [(ctx["a"]["id"], 3)])  # sobram 2
    assert retry(client, ctx, failed["id"]).status_code == 409
    assert client.get(f"/api/orders/{failed['id']}", headers=ctx["h"]).json()["status"] == "FAILED"
    assert stock(client, ctx["a"]["id"]) == 2


def test_retry_access_and_validation(client, ctx):
    use_gateway("always")
    failed = checkout(client, ctx["h"], [(ctx["a"]["id"], 1)]).json()
    other, _ = login_user(client, BUYER_2)
    assert retry(client, ctx, failed["id"], headers=other).status_code == 403
    assert retry(client, ctx, 999).status_code == 404
    assert retry(client, ctx, failed["id"], method="PIX").status_code == 422


def test_retry_claims_with_conditional_update(session, ctx, sql_log):
    from app.modules.orders import service

    use_gateway("always")
    failed = service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 1)],
                              service.Address(**ADDRESS), service.ShippingMethod.STANDARD,
                              service.PaymentMethod.CARD)
    use_gateway("none")
    sql_log.clear()
    assert service.retry_payment(session, failed.id, ctx["uid"], service.PaymentMethod.GIFT).status == "PAID"
    claims = [s for s in sql_log if s.upper().startswith('UPDATE "ORDER"') and "status" in s.lower()]
    assert claims and "where" in claims[0].lower() and "status =" in claims[0].lower().split("where", 1)[1], (
        "a retentativa precisa reivindicar o pedido com UPDATE ... WHERE status = 'FAILED'"
    )


def test_service_errors(session, ctx):
    from app.core.errors import ForbiddenError, NotFoundError
    from app.modules.orders import service

    order = service.checkout(session, ctx["uid"], [service.CheckoutItem(ctx["a"]["id"], 1)],
                             service.Address(**ADDRESS), service.ShippingMethod.STANDARD,
                             service.PaymentMethod.CARD)
    assert service.get_order(session, order.id, ctx["uid"]).id == order.id
    with pytest.raises(ForbiddenError):
        service.get_order(session, order.id, ctx["uid"] + 100)
    with pytest.raises(NotFoundError):
        service.get_order(session, 999, ctx["uid"])
    assert [o.id for o in service.list_by_buyer(session, ctx["uid"])] == [order.id]
