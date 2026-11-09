"""Fluxo completo de compra, só por HTTP."""
from tests.conftest import ADDRESS, BUYER, SELLER, checkout, create_product, login_user


def test_full_purchase_flow(client):
    seller, seller_id = login_user(client, SELLER)
    buyer, buyer_id = login_user(client, BUYER)

    # 1. catálogo
    notebook = create_product(client, seller, name="Notebook Aurora 14", brand="Aurora", category="Eletrônicos",
                              price_cents=450000, stock=3, description=None)
    mouse = create_product(client, seller, name="Mouse Aurora sem fio", brand="Aurora", category="Eletrônicos",
                           price_cents=9900, stock=10, description=None)
    create_product(client, seller, name="Livro de Receitas", category="Livros", price_cents=5900, description=None)

    # 2. busca, produto e relacionados
    found = client.get("/api/search/products", params={"q": "notebok"}).json()
    assert found["corrected_query"] == "notebook"
    assert [p["id"] for p in found["items"]] == [notebook["id"]]
    assert client.get(f"/api/catalog/products/{notebook['id']}").json()["stock"] == 3
    related = client.get(f"/api/catalog/products/{notebook['id']}/related").json()
    assert related[0]["product"]["id"] == mouse["id"]
    assert "SAME_BRAND" in related[0]["reasons"]

    # 3. carrinho e checkout
    cart = f"/api/cart/{buyer_id}"
    client.post(f"{cart}/items", json={"product_id": notebook["id"], "quantity": 1}, headers=buyer)
    client.post(f"{cart}/items", json={"product_id": mouse["id"], "quantity": 2}, headers=buyer)
    body = client.post(f"{cart}/items/{mouse['id']}/save-for-later", headers=buyer).json()
    assert body["total_cents"] == 450000
    to_buy = [(i["product_id"], i["quantity"]) for i in body["items"]]
    order = checkout(client, buyer, to_buy, key="pedido-1").json()
    assert order["status"] == "PAID"
    assert order["total_cents"] == 450000
    assert checkout(client, buyer, to_buy, key="pedido-1").json()["id"] == order["id"]  # clique duplo
    client.delete(f"{cart}/items/{notebook['id']}", headers=buyer)

    # 4. estoque, histórico e painel do vendedor
    assert client.get(f"/api/catalog/products/{notebook['id']}").json()["stock"] == 2
    assert [o["id"] for o in client.get("/api/orders", headers=buyer).json()] == [order["id"]]
    received = client.get(f"/api/sellers/{seller_id}/orders", headers=seller).json()
    assert received[0]["id"] == order["id"]
    assert received[0]["subtotal_cents"] == 450000
    assert client.get(f"/api/sellers/{seller_id}/metrics", headers=seller).json()["total_revenue_cents"] == 450000

    # 5. envio e endereço travado
    for status in ("SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"):
        r = client.post(f"/api/sellers/{seller_id}/orders/{order['id']}/fulfillment",
                        json={"status": status}, headers=seller)
        assert r.status_code == 200, r.text
    r = client.patch(f"/api/orders/{order['id']}/address", json=ADDRESS, headers=buyer)
    assert r.status_code == 409
    assert client.get(f"/api/orders/{order['id']}", headers=buyer).json()["fulfillment_status"] == "DELIVERED"

    # 6. avaliação e nota no catálogo/busca
    r = client.post(f"/api/reviews/products/{notebook['id']}", json={"stars": 5, "title": "Excelente"}, headers=buyer)
    assert r.status_code == 201
    assert r.json()["author_name"] == BUYER["name"]
    assert client.get(f"/api/catalog/products/{notebook['id']}").json()["average_rating"] == 5.0
    top = client.get("/api/search/products", params={"sort": "rating"}).json()["items"][0]
    assert top["id"] == notebook["id"]

    # 7. pagamento recusado e nova tentativa
    from app.modules.payments import service as payments

    payments.set_gateway(payments.MockPaymentGateway("first-attempt"))
    failed = checkout(client, buyer, [(notebook["id"], 2)]).json()
    assert failed["status"] == "FAILED"
    assert client.get(f"/api/catalog/products/{notebook['id']}").json()["stock"] == 2
    paid = client.post(f"/api/orders/{failed['id']}/payment", json={"payment_method": "GIFT"}, headers=buyer).json()
    assert paid["status"] == "PAID"
    assert client.get(f"/api/catalog/products/{notebook['id']}").json()["stock"] == 0
    assert len(client.get("/api/orders", headers=buyer).json()) == 2


def test_health_and_openapi(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    paths = client.get("/openapi.json").json()["paths"]
    for prefix in ("/api/users", "/api/catalog", "/api/search", "/api/cart", "/api/orders", "/api/reviews",
                   "/api/sellers"):
        assert any(p.startswith(prefix) for p in paths), f"nenhuma rota em {prefix}"
