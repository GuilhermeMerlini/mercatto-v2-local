import pytest

from app.core.errors import InsufficientStockError, InvalidInputError, NotFoundError


@pytest.fixture(name="product")
def product_fixture(session):
    from app.modules.catalog import service

    data = service.ProductData(name="Caneca", price_cents=3000, stock=5, category="Casa")
    return service.create_product(session, 1, data)


@pytest.fixture(name="catalog")
def catalog_fixture():
    from app.modules.catalog import service

    return service


def stock(catalog, session, product_id):
    return catalog.get_product(session, product_id).stock


# ---------- decrease_stock ----------


def test_decrease_stock(catalog, session, product):
    catalog.decrease_stock(session, product.id, 2)
    assert stock(catalog, session, product.id) == 3


def test_decrease_whole_stock_is_allowed(catalog, session, product):
    catalog.decrease_stock(session, product.id, 5)
    assert stock(catalog, session, product.id) == 0


def test_decrease_more_than_stock_keeps_stock_intact(catalog, session, product):
    with pytest.raises(InsufficientStockError):
        catalog.decrease_stock(session, product.id, 6)
    assert stock(catalog, session, product.id) == 5


def test_decrease_on_empty_stock_fails(catalog, session, product):
    catalog.decrease_stock(session, product.id, 5)
    with pytest.raises(InsufficientStockError):
        catalog.decrease_stock(session, product.id, 1)


def test_decrease_missing_product(catalog, session):
    with pytest.raises(NotFoundError):
        catalog.decrease_stock(session, 999, 1)


@pytest.mark.parametrize("qty", [0, -1])
def test_decrease_invalid_qty(catalog, session, product, qty):
    with pytest.raises(InvalidInputError):
        catalog.decrease_stock(session, product.id, qty)


def test_insufficient_stock_is_a_conflict():
    from app.core.errors import ConflictError

    assert issubclass(InsufficientStockError, ConflictError)


def test_decrease_is_a_single_conditional_update(catalog, session, product, sql_log):
    sql_log.clear()
    catalog.decrease_stock(session, product.id, 1)
    updates = [s for s in sql_log if s.upper().startswith("UPDATE PRODUCT")]
    assert updates, f"esperado um UPDATE em product; SQL executado: {sql_log}"
    assert any("stock >=" in s.lower() for s in updates), (
        "a baixa precisa ser um UPDATE condicional (WHERE ... stock >= ?), não ler-subtrair-salvar"
    )


def test_view_is_fresh_after_update_in_same_session(catalog, session, product):
    catalog.get_product(session, product.id)  # carrega na sessão
    catalog.decrease_stock(session, product.id, 4)
    assert catalog.get_product(session, product.id).stock == 1


# ---------- increase_stock ----------


def test_increase_stock(catalog, session, product):
    catalog.decrease_stock(session, product.id, 5)
    catalog.increase_stock(session, product.id, 2)
    assert stock(catalog, session, product.id) == 2


def test_increase_missing_and_invalid(catalog, session, product):
    with pytest.raises(NotFoundError):
        catalog.increase_stock(session, 999, 1)
    with pytest.raises(InvalidInputError):
        catalog.increase_stock(session, product.id, 0)


# ---------- update_rating ----------


def test_update_rating(catalog, session, product):
    catalog.update_rating(session, product.id, 4.3333333, 3)
    view = catalog.get_product(session, product.id)
    assert view.average_rating == 4.33
    assert view.review_count == 3


def test_update_rating_shows_in_api(client, catalog, session, product):
    catalog.update_rating(session, product.id, 5.0, 1)
    body = client.get(f"/api/catalog/products/{product.id}").json()
    assert (body["average_rating"], body["review_count"]) == (5.0, 1)


def test_rating_survives_product_edit(catalog, session, product):
    catalog.update_rating(session, product.id, 4.0, 2)
    data = catalog.ProductData(name="Caneca grande", price_cents=3500, stock=5, category="Casa")
    updated = catalog.update_product(session, product.id, 1, data)
    assert (updated.average_rating, updated.review_count) == (4.0, 2)
