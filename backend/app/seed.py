import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.db import engine
from app.core.errors import ConflictError
from app.modules.catalog import service as catalog
from app.modules.users import service as users


def seed(session: Session, limit: Optional[int] = None) -> dict:
    # O seller1 funciona como marcador: se já existe, o seed já rodou.
    try:
        seller1 = users.register(session, "Seller 1", "seller1@mercatto.dev", "mercatto123", "SELLER")
    except ConflictError:
        return {"users": 0, "products": 0}
    seller2 = users.register(session, "Seller 2", "seller2@mercatto.dev", "mercatto123", "SELLER")
    users.register(session, "Buyer", "buyer@mercatto.dev", "mercatto123", "BUYER")

    # Read and create products
    products_created = 0
    seller_ids = [seller1.id, seller2.id]
    seller_index = 0

    csv_path = Path(__file__).parent / "seed_data" / "products.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit is not None and products_created >= limit:
                break

            try:
                price = Decimal(row["price"])
            except (InvalidOperation, KeyError, TypeError):
                continue
            if not price.is_finite() or price <= 0:
                continue

            price_cents = round(price * 100)
            name = row["name"]
            brand = name.split()[0] if name else None

            product_data = catalog.ProductData(
                name=name,
                price_cents=price_cents,
                stock=int(row["stock_quantity"]),
                category=row["category"],
                image_url=row["image_url"],
                brand=brand,
            )

            seller_id = seller_ids[seller_index]
            catalog.create_product(session, seller_id, product_data)
            products_created += 1
            seller_index = (seller_index + 1) % len(seller_ids)

    return {"users": 3, "products": products_created}


if __name__ == "__main__":
    from app.core.db import init_db

    init_db()
    with Session(engine) as session:
        result = seed(session)
        print(result)
