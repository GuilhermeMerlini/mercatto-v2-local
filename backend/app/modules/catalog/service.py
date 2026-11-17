from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, InvalidInputError, NotFoundError
from app.modules.catalog.models import Product


@dataclass(frozen=True)
class ProductData:
    name: str
    price_cents: int
    stock: int
    category: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    warranty_months: Optional[int] = None
    model_number: Optional[str] = None
    list_price_cents: Optional[int] = None


@dataclass(frozen=True)
class ProductView:
    id: int
    name: str
    description: Optional[str]
    price_cents: int
    list_price_cents: Optional[int]
    stock: int
    category: str
    image_url: Optional[str]
    brand: Optional[str]
    warranty_months: Optional[int]
    model_number: Optional[str]
    seller_id: int
    average_rating: float
    review_count: int
    created_at: datetime


def _to_view(product: Product) -> ProductView:
    return ProductView(**{f.name: getattr(product, f.name) for f in fields(ProductView)})


def _validated(data: ProductData) -> ProductData:
    """Valida os campos editáveis e devolve uma cópia com `name` e `category` sem espaços nas pontas."""
    if not data.name or not data.name.strip():
        raise InvalidInputError("Name cannot be empty or only whitespace")
    if not data.category or not data.category.strip():
        raise InvalidInputError("Category cannot be empty or only whitespace")
    if data.price_cents <= 0:
        raise InvalidInputError("Price must be greater than zero")
    if data.stock < 0:
        raise InvalidInputError("Stock cannot be negative")
    if data.list_price_cents is not None and data.list_price_cents <= data.price_cents:
        raise InvalidInputError("List price must be greater than price")
    return replace(data, name=data.name.strip(), category=data.category.strip())


def _owned_product(session: Session, product_id: int, seller_id: int) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found")
    if product.seller_id != seller_id:
        raise ForbiddenError("You are not the owner of this product")
    return product


def _paginate(session: Session, stmt, page: int, page_size: int) -> tuple[list[ProductView], int]:
    if page < 1:
        raise InvalidInputError("Page must be >= 1")
    if page_size < 1:
        raise InvalidInputError("Page size must be >= 1")
    if page_size > 100:
        raise InvalidInputError("Page size must be <= 100")
    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    products = session.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return [_to_view(p) for p in products], total


def create_product(session: Session, seller_id: int, data: ProductData) -> ProductView:
    product = Product(**asdict(_validated(data)), seller_id=seller_id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _to_view(product)


def update_product(session: Session, product_id: int, seller_id: int, data: ProductData) -> ProductView:
    product = _owned_product(session, product_id, seller_id)
    for field, value in asdict(_validated(data)).items():
        setattr(product, field, value)
    session.commit()
    session.refresh(product)
    return _to_view(product)


def delete_product(session: Session, product_id: int, seller_id: int) -> None:
    session.delete(_owned_product(session, product_id, seller_id))
    session.commit()


def get_product(session: Session, product_id: int) -> ProductView:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found")
    return _to_view(product)


def find_product(session: Session, product_id: int) -> Optional[ProductView]:
    product = session.get(Product, product_id)
    return _to_view(product) if product else None


def list_products(
    session: Session, category: Optional[str] = None, page: int = 1, page_size: int = 20
) -> tuple[list[ProductView], int]:
    stmt = select(Product).order_by(Product.id)
    if category is not None:
        stmt = stmt.where(Product.category == category)
    return _paginate(session, stmt, page, page_size)


def list_by_seller(
    session: Session, seller_id: int, page: int = 1, page_size: int = 20
) -> tuple[list[ProductView], int]:
    stmt = select(Product).where(Product.seller_id == seller_id).order_by(Product.id)
    return _paginate(session, stmt, page, page_size)


def list_categories(session: Session) -> list[str]:
    stmt = select(Product.category).distinct().order_by(Product.category)
    return list(session.execute(stmt).scalars().all())


def get_many(session: Session, ids: list[int]) -> list[ProductView]:
    if not ids:
        return []
    stmt = select(Product).where(Product.id.in_(ids)).order_by(Product.id)
    return [_to_view(p) for p in session.execute(stmt).scalars().all()]


def filter_products(
    session: Session,
    category: Optional[str] = None,
    min_price_cents: Optional[int] = None,
    max_price_cents: Optional[int] = None,
    min_rating: Optional[float] = None,
) -> list[ProductView]:
    stmt = select(Product).order_by(Product.id)
    if category is not None:
        stmt = stmt.where(Product.category == category)
    if min_price_cents is not None:
        stmt = stmt.where(Product.price_cents >= min_price_cents)
    if max_price_cents is not None:
        stmt = stmt.where(Product.price_cents <= max_price_cents)
    if min_rating is not None:
        stmt = stmt.where(Product.average_rating >= min_rating)
    return [_to_view(p) for p in session.execute(stmt).scalars().all()]
