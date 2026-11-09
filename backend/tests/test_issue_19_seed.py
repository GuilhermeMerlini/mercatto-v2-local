import csv
from decimal import Decimal
from pathlib import Path

import pytest

CSV = Path(__file__).resolve().parent.parent / "app" / "seed_data" / "products.csv"


@pytest.fixture(name="seed")
def seed_fixture():
    from app import seed

    return seed


def first_rows(n):
    with CSV.open(newline="", encoding="utf-8") as f:
        return [row for _, row in zip(range(n), csv.DictReader(f))]


def test_seed_creates_users_and_products(session, seed):
    from app.modules.catalog import service as catalog

    assert seed.seed(session, limit=10) == {"users": 3, "products": 10}
    items, total = catalog.list_products(session, page=1, page_size=100)
    assert total == 10
    row = first_rows(1)[0]
    first = items[0]
    assert first.name == row["name"]
    assert first.price_cents == int(round(Decimal(row["price"]) * 100))
    assert first.stock == int(row["stock_quantity"])
    assert first.category == row["category"]
    assert first.image_url == row["image_url"]
    assert first.brand == row["name"].split()[0]


def test_seed_is_idempotent(session, seed):
    seed.seed(session, limit=3)
    assert seed.seed(session, limit=3) == {"users": 0, "products": 0}


def test_seed_users_can_log_in(client, session, seed):
    seed.seed(session, limit=2)
    for email, role in [("seller1@mercatto.dev", "SELLER"), ("seller2@mercatto.dev", "SELLER"),
                        ("buyer@mercatto.dev", "BUYER")]:
        r = client.post("/api/users/login", json={"email": email, "password": "mercatto123"})
        assert r.status_code == 200, email
        assert r.json()["role"] == role


def test_products_alternate_between_sellers(session, seed):
    from app.modules.catalog import service as catalog
    from app.modules.users import service as users

    seed.seed(session, limit=4)
    items, _ = catalog.list_products(session, page=1, page_size=10)
    sellers = [p.seller_id for p in items]
    assert len(set(sellers)) == 2
    assert sellers[0] == sellers[2] != sellers[1] == sellers[3]
    assert {users.get_user(session, s).role for s in sellers} == {"SELLER"}


def test_full_seed_loads_the_csv(session, seed):
    with CSV.open(newline="", encoding="utf-8") as f:
        valid = sum(1 for row in csv.DictReader(f) if Decimal(row["price"]) > 0)
    assert seed.seed(session)["products"] == valid


def test_seed_uses_only_services():
    source = (Path(__file__).resolve().parent.parent / "app" / "seed.py").read_text()
    assert ".models" not in source
