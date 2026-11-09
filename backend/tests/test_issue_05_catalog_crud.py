import ast
import dataclasses
from pathlib import Path

import pytest
from sqlmodel import SQLModel

from tests.conftest import BUYER, PRODUCT, SELLER, SELLER_2, create_product, login_user

CATALOG = Path(__file__).resolve().parent.parent / "app" / "modules" / "catalog"
PRODUCT_FIELDS = {
    "id", "name", "description", "price_cents", "list_price_cents", "stock", "category", "image_url",
    "brand", "warranty_months", "model_number", "seller_id", "average_rating", "review_count", "created_at",
}


@pytest.fixture(name="seller")
def seller_fixture(client):
    return login_user(client, SELLER)


# ---------- criar ----------


def test_seller_creates_product(client, seller):
    headers, seller_id = seller
    r = client.post("/api/catalog/products", json=PRODUCT, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert set(body) == PRODUCT_FIELDS
    assert body["seller_id"] == seller_id
    assert body["price_cents"] == 450000
    assert body["average_rating"] == 0
    assert body["review_count"] == 0
    assert body["list_price_cents"] is None


def test_create_with_all_optional_fields(client, seller):
    extra = {"list_price_cents": 500000, "image_url": "https://img.example/x.jpg",
             "warranty_months": 12, "model_number": "AU-14"}
    body = create_product(client, seller[0], **extra)
    for key, value in extra.items():
        assert body[key] == value


def test_create_strips_name_and_category(client, seller):
    body = create_product(client, seller[0], name="  Mouse  ", category=" Periféricos ")
    assert body["name"] == "Mouse"
    assert body["category"] == "Periféricos"


def test_buyer_cannot_create_product(client):
    headers, _ = login_user(client, BUYER)
    assert client.post("/api/catalog/products", json=PRODUCT, headers=headers).status_code == 403


def test_create_without_token_returns_401(client):
    assert client.post("/api/catalog/products", json=PRODUCT).status_code == 401


@pytest.mark.parametrize(
    "overrides",
    [
        {"price_cents": 0},
        {"price_cents": -10},
        {"stock": -1},
        {"name": ""},
        {"category": ""},
        {"warranty_months": -1},
        {"list_price_cents": 0},
        {"name": "x" * 256},
        {"description": "x" * 2001},
    ],
)
def test_create_invalid_input_returns_422(client, seller, overrides):
    r = client.post("/api/catalog/products", json={**PRODUCT, **overrides}, headers=seller[0])
    assert r.status_code == 422


def test_create_missing_field_returns_422(client, seller):
    body = {k: v for k, v in PRODUCT.items() if k != "category"}
    assert client.post("/api/catalog/products", json=body, headers=seller[0]).status_code == 422


@pytest.mark.parametrize("list_price", [450000, 400000])
def test_list_price_not_above_price_returns_400(client, seller, list_price):
    r = client.post("/api/catalog/products", json={**PRODUCT, "list_price_cents": list_price},
                    headers=seller[0])
    assert r.status_code == 400


def test_blank_name_is_rejected(client, seller):
    r = client.post("/api/catalog/products", json={**PRODUCT, "name": "   "}, headers=seller[0])
    assert r.status_code in (400, 422)


# ---------- ler ----------


def test_get_product_is_public(client, seller):
    created = create_product(client, seller[0])
    r = client.get(f"/api/catalog/products/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_product_returns_404(client):
    assert client.get("/api/catalog/products/999").status_code == 404


# ---------- atualizar ----------


def test_owner_updates_product_replacing_fields(client, seller):
    created = create_product(client, seller[0], image_url="https://img.example/a.jpg")
    changes = {"name": "Notebook Aurora 15", "price_cents": 399900, "stock": 2, "category": "Informática"}
    r = client.put(f"/api/catalog/products/{created['id']}", json=changes, headers=seller[0])
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Notebook Aurora 15"
    assert body["price_cents"] == 399900
    assert body["category"] == "Informática"
    assert body["image_url"] is None  # PUT substitui: campo omitido volta a None
    assert body["id"] == created["id"]
    assert body["seller_id"] == created["seller_id"]
    assert client.get(f"/api/catalog/products/{created['id']}").json()["name"] == "Notebook Aurora 15"


def test_other_seller_cannot_update(client, seller):
    created = create_product(client, seller[0])
    other, _ = login_user(client, SELLER_2)
    r = client.put(f"/api/catalog/products/{created['id']}", json=PRODUCT, headers=other)
    assert r.status_code == 403


def test_buyer_cannot_update(client, seller):
    created = create_product(client, seller[0])
    buyer, _ = login_user(client, BUYER)
    assert client.put(f"/api/catalog/products/{created['id']}", json=PRODUCT, headers=buyer).status_code == 403


def test_update_missing_product_returns_404(client, seller):
    assert client.put("/api/catalog/products/999", json=PRODUCT, headers=seller[0]).status_code == 404


def test_update_validates_like_create(client, seller):
    created = create_product(client, seller[0])
    url = f"/api/catalog/products/{created['id']}"
    assert client.put(url, json={**PRODUCT, "price_cents": 0}, headers=seller[0]).status_code == 422
    assert client.put(url, json={**PRODUCT, "list_price_cents": 1}, headers=seller[0]).status_code == 400


# ---------- excluir ----------


def test_owner_deletes_product(client, seller):
    created = create_product(client, seller[0])
    r = client.delete(f"/api/catalog/products/{created['id']}", headers=seller[0])
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/api/catalog/products/{created['id']}").status_code == 404


def test_other_seller_cannot_delete(client, seller):
    created = create_product(client, seller[0])
    other, _ = login_user(client, SELLER_2)
    assert client.delete(f"/api/catalog/products/{created['id']}", headers=other).status_code == 403
    assert client.get(f"/api/catalog/products/{created['id']}").status_code == 200


def test_delete_missing_returns_404_and_requires_token(client, seller):
    assert client.delete("/api/catalog/products/999", headers=seller[0]).status_code == 404
    assert client.delete("/api/catalog/products/1").status_code == 401


# ---------- service ----------


def test_service_types_are_frozen_dataclasses(session):
    from app.modules.catalog import service

    view = service.create_product(session, 1, service.ProductData(name="Livro", price_cents=5000,
                                                                  stock=3, category="Livros"))
    assert dataclasses.is_dataclass(view)
    assert {f.name for f in dataclasses.fields(view)} == PRODUCT_FIELDS
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.stock = 0
    assert service.ProductData(name="a", price_cents=1, stock=0, category="b").brand is None


def test_service_errors(session):
    from app.core.errors import ForbiddenError, InvalidInputError, NotFoundError
    from app.modules.catalog import service

    data = service.ProductData(name="Livro", price_cents=5000, stock=3, category="Livros")
    view = service.create_product(session, 1, data)
    assert service.get_product(session, view.id) == view
    assert service.find_product(session, 999) is None
    with pytest.raises(NotFoundError):
        service.get_product(session, 999)
    with pytest.raises(ForbiddenError):
        service.update_product(session, view.id, 2, data)
    with pytest.raises(ForbiddenError):
        service.delete_product(session, view.id, 2)
    with pytest.raises(InvalidInputError):
        service.create_product(session, 1, dataclasses.replace(data, name="  "))
    with pytest.raises(InvalidInputError):
        service.create_product(session, 1, dataclasses.replace(data, stock=-1))
    with pytest.raises(NotFoundError):
        service.delete_product(session, 999, 1)


def test_product_table_is_registered():
    import app.modules.registry  # noqa: F401

    assert "product" in SQLModel.metadata.tables


def test_service_does_not_import_fastapi_and_router_has_no_http_exception():
    tree = ast.parse((CATALOG / "service.py").read_text())
    imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imported += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(m.split(".")[0] in {"fastapi", "starlette"} for m in imported)
    assert "HTTPException" not in (CATALOG / "router.py").read_text()


def test_model_has_no_relationship():
    assert "Relationship" not in (CATALOG / "models.py").read_text()
