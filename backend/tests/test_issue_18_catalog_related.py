from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.modules.catalog import related
from tests.conftest import SELLER, create_product, login_user

R = related.RelatedReason


def view(id, name="Produto", category="Casa", brand=None, price_cents=10000, rating=0.0, count=0, stock=10):
    return SimpleNamespace(id=id, name=name, category=category, brand=brand, price_cents=price_cents,
                           average_rating=rating, review_count=count, stock=stock)


# ---------- funções puras ----------


def test_reason_priority_order():
    assert [r.value for r in R] == ["TOP_RATED_IN_CATEGORY", "LOWER_PRICE", "SAME_BRAND", "SIMILAR_NAME",
                                    "HIGHER_RATED", "SAME_CATEGORY"]


def test_name_tokens():
    assert related.name_tokens("The Wireless Mouse for Men, 2 Pack 2024") == {"wireless", "mouse"}
    assert related.name_tokens(None) == set()


def test_longest_name_tokens():
    assert related.longest_name_tokens("Cafeteira Elétrica Inox Compacta", 2) == ["cafeteira", "compacta"]


@pytest.mark.parametrize(
    "brand, expected",
    [("Aurora", True), ("Women's", False), ("Women’s", False), ("3-Pack", False), ("", False), (None, False),
     ("Wireless", False), ("pack", False), ("  Logi ", True)],
)
def test_is_real_brand(brand, expected):
    assert related.is_real_brand(brand) is expected


def test_same_brand():
    assert related.same_brand("Aurora", " aurora ")
    assert not related.same_brand("Aurora", "Lumen")
    assert not related.same_brand("Wireless", "Wireless")


def test_score_maximum_points():
    current = view(1, "Caneca Térmica Azul", brand="Termo", price_cents=5000)
    twin = view(2, "Caneca Térmica Azul", brand="Termo", price_cents=5000)
    assert related.score(current, twin, None).score == pytest.approx(8.5)
    reviewed = view(3, "Caneca Térmica Azul", brand="Termo", price_cents=5000, rating=5.0, count=1)
    assert related.score(current, reviewed, None).score == pytest.approx(9.5)


def test_score_components():
    current = view(1, "Caneca", category="Casa", price_cents=10000)
    # outra categoria, preço 50% maior, nome diferente: só 1.5 * 0.5 de preço
    other = view(2, "Livro", category="Livros", price_cents=15000)
    assert related.score(current, other, None).score == pytest.approx(0.75)
    # preço com 100%+ de diferença não pontua
    assert related.score(current, view(3, "Livro", category="Livros", price_cents=30000), None).score == 0
    # preço atual zero não pontua nem quebra
    assert related.score(view(4, "X", price_cents=0), view(5, "Y", category="Z"), None).score == 0


def test_reasons_in_priority_order():
    current = view(1, "Caneca Térmica Azul", brand="Termo", price_cents=5000, rating=3.0, count=2)
    candidate = view(2, "Caneca Térmica Verde", brand="Termo", price_cents=4000, rating=4.5, count=4)
    scored = related.score(current, candidate, category_top_rating=4.5)
    assert scored.reasons == [R.TOP_RATED_IN_CATEGORY, R.LOWER_PRICE, R.SAME_BRAND, R.SIMILAR_NAME,
                              R.HIGHER_RATED, R.SAME_CATEGORY]


def test_reasons_need_evidence():
    current = view(1, "Caneca Azul", price_cents=5000)
    unreviewed = view(2, "Caneca Verde", price_cents=6000)  # 1 token em comum, mais cara, sem avaliações
    assert related.score(current, unreviewed, category_top_rating=4.0).reasons == [R.SAME_CATEGORY]
    other_cat = view(3, "Livro Barato", category="Livros", price_cents=10)
    assert related.score(current, other_cat, None).reasons == []  # mais barato, mas outra categoria


def test_sort_key():
    a = related.score(view(1, "A"), view(5, "B", count=0), None)
    b = related.score(view(1, "A"), view(3, "C", count=7), None)
    c = related.score(view(1, "A"), view(2, "D", count=7), None)
    assert [s.product.id for s in sorted([a, b, c], key=related.sort_key)] == [2, 3, 5]


# ---------- endpoint ----------


@pytest.fixture(name="shop")
def shop_fixture(client, session):
    h, _ = login_user(client, SELLER)

    def make(name, category="Cozinha", brand=None, price=5000, stock=10, description=None):
        return create_product(client, h, name=name, category=category, brand=brand, price_cents=price,
                              stock=stock, description=description)

    p = {
        "current": make("Caneca Térmica Azul", brand="Termo"),
        "twin": make("Caneca Térmica Verde", brand="Termo", price=4500),
        "pan": make("Frigideira Antiaderente", price=9000),
        "sold_out": make("Caneca Térmica Rosa", brand="Termo", stock=0),
        "cross_brand": make("Garrafa de Viagem", category="Esportes", brand="Termo"),
        "cross_name": make("Adesivo Caneca Térmica", category="Papelaria", price=500),
        "unrelated": make("Bola de Futebol", category="Esportes"),
    }
    session.execute(text("UPDATE product SET average_rating = 4.0, review_count = 2 WHERE id = :id"),
                    {"id": p["pan"]["id"]})
    session.commit()
    return p


def related_ids(client, product_id, **params):
    r = client.get(f"/api/catalog/products/{product_id}/related", params=params)
    assert r.status_code == 200, r.text
    return [x["product"]["id"] for x in r.json()]


def test_same_category_first_then_cross_category_with_reason(client, shop):
    ids = related_ids(client, shop["current"]["id"], limit=6)
    assert ids[:2] == [shop["twin"]["id"], shop["pan"]["id"]]
    assert set(ids[2:]) == {shop["cross_brand"]["id"], shop["cross_name"]["id"]}
    assert shop["sold_out"]["id"] not in ids
    assert shop["unrelated"]["id"] not in ids
    assert shop["current"]["id"] not in ids


def test_cross_category_only_when_same_category_is_not_enough(client, shop):
    assert related_ids(client, shop["current"]["id"], limit=2) == [shop["twin"]["id"], shop["pan"]["id"]]


def test_payload(client, shop):
    first = client.get(f"/api/catalog/products/{shop['current']['id']}/related").json()[0]
    assert set(first) == {"product", "score", "primary_reason", "reasons"}
    assert first["product"]["name"] == "Caneca Térmica Verde"
    assert first["primary_reason"] == "LOWER_PRICE"
    assert first["reasons"][0] == first["primary_reason"]
    assert "SAME_BRAND" in first["reasons"] and "SIMILAR_NAME" in first["reasons"]
    assert first["score"] == round(first["score"], 3)


def test_top_rated_reason(client, shop):
    by_id = {x["product"]["id"]: x for x in client.get(f"/api/catalog/products/{shop['current']['id']}/related").json()}
    assert by_id[shop["pan"]["id"]]["reasons"][0] == "TOP_RATED_IN_CATEGORY"


def test_no_padding_with_unrelated_products(client, shop):
    # só a garrafa é da mesma categoria; nada de outra categoria tem marca ou nome em comum
    assert related_ids(client, shop["unrelated"]["id"]) == [shop["cross_brand"]["id"]]


def test_errors(client, shop):
    assert client.get("/api/catalog/products/999/related").status_code == 404
    url = f"/api/catalog/products/{shop['current']['id']}/related"
    assert client.get(url, params={"limit": 0}).status_code == 422
    assert client.get(url, params={"limit": 21}).status_code == 422


def test_service_find_related(session, shop):
    from app.core.errors import NotFoundError
    from app.modules.catalog import service

    results = service.find_related(session, shop["current"]["id"], limit=1)
    assert len(results) == 1
    assert results[0].product.id == shop["twin"]["id"]
    assert results[0].primary_reason == service.RelatedReason.LOWER_PRICE
    with pytest.raises(NotFoundError):
        service.find_related(session, 999)
