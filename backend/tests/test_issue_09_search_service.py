import ast
from pathlib import Path

import pytest
from sqlalchemy import text

from tests.conftest import SELLER, login_user
from tests.conftest import create_product as make

SEARCH = Path(__file__).resolve().parent.parent / "app" / "modules" / "search"
URL = "/api/search/products"


@pytest.fixture(name="catalog")
def catalog_fixture(client, session):
    """Seis produtos com preços, categorias e notas conhecidos."""
    headers, _ = login_user(client, SELLER)

    def create_product(client, headers, **kw):  # sem a descrição padrão do helper
        return make(client, headers, **{"description": None, **kw})

    p = {}
    p["notebook"] = create_product(client, headers, name="Notebook Aurora 14", brand="Aurora",
                                   category="Eletrônicos", price_cents=450000)
    p["mouse"] = create_product(client, headers, name="Mouse sem fio", brand="Logi",
                                category="Eletrônicos", price_cents=9900)
    p["capa"] = create_product(client, headers, name="Capa para notebook 14", brand="Bolsa",
                               category="Acessórios", price_cents=12000)
    p["livro"] = create_product(client, headers, name="Livro de Receitas", brand="Editora",
                                category="Livros", price_cents=5900, description="receitas rápidas")
    p["camera"] = create_product(client, headers, name="Câmera Fotográfica", brand="Lumen",
                                 category="Eletrônicos", price_cents=250000)
    p["caneca"] = create_product(client, headers, name="Caneca Térmica", brand="Casa",
                                 category="Casa", price_cents=9900)
    for key, rating, count in [("mouse", 4.8, 10), ("camera", 4.8, 3), ("livro", 3.0, 2)]:
        session.execute(text("UPDATE product SET average_rating = :r, review_count = :c WHERE id = :id"),
                        {"r": rating, "c": count, "id": p[key]["id"]})
    session.commit()
    return p


def ids(r):
    assert r.status_code == 200, r.text
    return [item["id"] for item in r.json()["items"]]


def test_response_shape(client, catalog):
    body = client.get(URL).json()
    assert set(body) == {"items", "total", "page", "page_size", "corrected_query"}
    assert body["total"] == 6
    assert body["corrected_query"] is None
    assert {"id", "name", "price_cents", "average_rating"} <= set(body["items"][0])


def test_without_query_returns_all_by_id(client, catalog):
    assert ids(client.get(URL)) == sorted(p["id"] for p in catalog.values())


def test_text_query_uses_relevance(client, catalog):
    # "notebook" no início do nome vem antes de "notebook" depois de "para"
    assert ids(client.get(URL, params={"q": "notebook"})) == [catalog["notebook"]["id"], catalog["capa"]["id"]]


def test_all_terms_must_match(client, catalog):
    assert ids(client.get(URL, params={"q": "notebook capa"})) == [catalog["capa"]["id"]]
    assert ids(client.get(URL, params={"q": "notebook gamer"})) == []


def test_query_ignores_accents(client, catalog):
    assert ids(client.get(URL, params={"q": "camera"})) == [catalog["camera"]["id"]]
    assert ids(client.get(URL, params={"q": "TÉRMICA"})) == [catalog["caneca"]["id"]]


def test_description_matches(client, catalog):
    assert ids(client.get(URL, params={"q": "rápidas"})) == [catalog["livro"]["id"]]


def test_typo_is_corrected(client, catalog):
    r = client.get(URL, params={"q": "camara"})
    assert ids(r) == [catalog["camera"]["id"]]
    assert r.json()["corrected_query"] == "camera"


def test_no_correction_when_nothing_close(client, catalog):
    r = client.get(URL, params={"q": "xylofone"})
    assert ids(r) == []
    assert r.json()["corrected_query"] is None


def test_filters(client, catalog):
    assert set(ids(client.get(URL, params={"category": "Eletrônicos"}))) == {
        catalog["notebook"]["id"], catalog["mouse"]["id"], catalog["camera"]["id"]}
    assert set(ids(client.get(URL, params={"min_price_cents": 12000, "max_price_cents": 250000}))) == {
        catalog["capa"]["id"], catalog["camera"]["id"]}
    assert set(ids(client.get(URL, params={"min_rating": 4}))) == {catalog["mouse"]["id"], catalog["camera"]["id"]}


def test_query_combined_with_filter(client, catalog):
    assert ids(client.get(URL, params={"q": "notebook", "category": "Acessórios"})) == [catalog["capa"]["id"]]


def test_sort_by_price(client, catalog):
    asc = ids(client.get(URL, params={"sort": "price_asc"}))
    # mouse e caneca têm o mesmo preço: desempate por id
    assert asc == [catalog[k]["id"] for k in ["livro", "mouse", "caneca", "capa", "camera", "notebook"]]
    desc = ids(client.get(URL, params={"sort": "PRICE_DESC"}))
    assert desc == [catalog[k]["id"] for k in ["notebook", "camera", "capa", "mouse", "caneca", "livro"]]


def test_sort_by_rating(client, catalog):
    order = ids(client.get(URL, params={"sort": "rating"}))
    assert order[:3] == [catalog["mouse"]["id"], catalog["camera"]["id"], catalog["livro"]["id"]]


def test_sort_applies_after_text_match(client, catalog):
    assert ids(client.get(URL, params={"q": "notebook", "sort": "price_asc"})) == [
        catalog["capa"]["id"], catalog["notebook"]["id"]]


def test_pagination(client, catalog):
    r = client.get(URL, params={"page": 2, "page_size": 4})
    body = r.json()
    assert (body["total"], body["page"], body["page_size"], len(body["items"])) == (6, 2, 4, 2)


@pytest.mark.parametrize(
    "params",
    [{"sort": "popular"}, {"min_price_cents": -1}, {"min_price_cents": 10, "max_price_cents": 5},
     {"min_rating": 6}, {"min_rating": -0.5}],
)
def test_invalid_filters_return_400(client, params):
    assert client.get(URL, params=params).status_code == 400


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 101}])
def test_invalid_pagination_returns_422(client, params):
    assert client.get(URL, params=params).status_code == 422


def test_service_search_products(session, catalog):
    from app.core.errors import InvalidInputError
    from app.modules.search import service

    result = service.search_products(session, query="notebook", page=1, page_size=1)
    assert (result.total, len(result.items), result.corrected_query) == (2, 1, None)
    assert result.items[0].id == catalog["notebook"]["id"]
    with pytest.raises(InvalidInputError):
        service.search_products(session, sort="nope")


def test_search_does_not_import_catalog_schemas_or_models():
    for name in ("service.py", "schemas.py", "router.py"):
        tree = ast.parse((SEARCH / name).read_text())
        imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not [m for m in imported if m.startswith("app.modules.catalog.") and m != "app.modules.catalog.service"]
