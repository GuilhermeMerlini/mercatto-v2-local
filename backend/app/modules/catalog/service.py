from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

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


def create_product(session: Session, seller_id: int, data: ProductData) -> ProductView:
    # Validations
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

    # Strip name and category
    data = replace(data, name=data.name.strip(), category=data.category.strip())

    product = Product(
        name=data.name,
        description=data.description,
        price_cents=data.price_cents,
        list_price_cents=data.list_price_cents,
        stock=data.stock,
        category=data.category,
        image_url=data.image_url,
        brand=data.brand,
        warranty_months=data.warranty_months,
        model_number=data.model_number,
        seller_id=seller_id,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return ProductView(
        id=product.id,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        list_price_cents=product.list_price_cents,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
        brand=product.brand,
        warranty_months=product.warranty_months,
        model_number=product.model_number,
        seller_id=product.seller_id,
        average_rating=product.average_rating,
        review_count=product.review_count,
        created_at=product.created_at,
    )


def update_product(session: Session, product_id: int, seller_id: int, data) -> ProductView:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found")
    if product.seller_id != seller_id:
        raise ForbiddenError("You are not the owner of this product")

    # Validations
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

    # Strip name and category
    data = replace(data, name=data.name.strip(), category=data.category.strip())

    product.name = data.name
    product.description = data.description
    product.price_cents = data.price_cents
    product.list_price_cents = data.list_price_cents
    product.stock = data.stock
    product.category = data.category
    product.image_url = data.image_url
    product.brand = data.brand
    product.warranty_months = data.warranty_months
    product.model_number = data.model_number

    session.commit()
    session.refresh(product)
    return ProductView(
        id=product.id,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        list_price_cents=product.list_price_cents,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
        brand=product.brand,
        warranty_months=product.warranty_months,
        model_number=product.model_number,
        seller_id=product.seller_id,
        average_rating=product.average_rating,
        review_count=product.review_count,
        created_at=product.created_at,
    )


def delete_product(session: Session, product_id: int, seller_id: int) -> None:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found")
    if product.seller_id != seller_id:
        raise ForbiddenError("You are not the owner of this product")
    session.delete(product)
    session.commit()


def get_product(session: Session, product_id: int) -> ProductView:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found")
    return ProductView(
        id=product.id,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        list_price_cents=product.list_price_cents,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
        brand=product.brand,
        warranty_months=product.warranty_months,
        model_number=product.model_number,
        seller_id=product.seller_id,
        average_rating=product.average_rating,
        review_count=product.review_count,
        created_at=product.created_at,
    )


def find_product(session: Session, product_id: int) -> Optional[ProductView]:
    product = session.get(Product, product_id)
    if not product:
        return None
    return ProductView(
        id=product.id,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        list_price_cents=product.list_price_cents,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
        brand=product.brand,
        warranty_months=product.warranty_months,
        model_number=product.model_number,
        seller_id=product.seller_id,
        average_rating=product.average_rating,
        review_count=product.review_count,
        created_at=product.created_at,
    )
