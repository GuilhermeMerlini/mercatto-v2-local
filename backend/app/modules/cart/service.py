from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.errors import InvalidInputError, NotFoundError
from app.modules.cart.models import CartItem
from app.modules.catalog import service as catalog


@dataclass(frozen=True)
class CartItemView:
    product_id: int
    product_name: str
    image_url: Optional[str]
    unit_price_cents: int
    quantity: int
    line_total_cents: int
    saved_for_later: bool


@dataclass(frozen=True)
class CartView:
    user_id: int
    items: list[CartItemView] = field(default_factory=list)
    saved_for_later: list[CartItemView] = field(default_factory=list)
    item_count: int = 0
    total_cents: int = 0


def _get_cart_items(session: Session, user_id: int) -> list[CartItem]:
    stmt = select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)
    return session.execute(stmt).scalars().all()


def _get_cart_item(session: Session, user_id: int, product_id: int) -> Optional[CartItem]:
    stmt = select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    return session.execute(stmt).scalars().one_or_none()


def _get_product_views(session: Session, product_ids: list[int]) -> dict[int, catalog.ProductView]:
    products = catalog.get_many(session, product_ids)
    return {p.id: p for p in products}


def get_cart(session: Session, user_id: int) -> CartView:
    items = _get_cart_items(session, user_id)
    product_ids = [item.product_id for item in items]
    product_views = _get_product_views(session, product_ids)
    cart_items = []
    saved_items = []
    item_count = 0
    total_cents = 0

    for item in items:
        product = product_views.get(item.product_id)
        if not product:
            continue
        line_total = product.price_cents * item.quantity
        item_view = CartItemView(
            product_id=item.product_id,
            product_name=product.name,
            image_url=product.image_url,
            unit_price_cents=product.price_cents,
            quantity=item.quantity,
            line_total_cents=line_total,
            saved_for_later=item.saved_for_later
        )
        if item.saved_for_later:
            saved_items.append(item_view)
        else:
            cart_items.append(item_view)
            item_count += item.quantity
            total_cents += line_total

    return CartView(
        user_id=user_id,
        items=cart_items,
        saved_for_later=saved_items,
        item_count=item_count,
        total_cents=total_cents
    )


def save_for_later(session: Session, user_id: int, product_id: int) -> CartView:
    cart_item = _get_cart_item(session, user_id, product_id)
    if not cart_item:
        raise NotFoundError("Item not found in cart")

    if not cart_item.saved_for_later:
        cart_item.saved_for_later = True
        cart_item.updated_at = utcnow()
        session.commit()

    return get_cart(session, user_id)


def move_to_cart(session: Session, user_id: int, product_id: int) -> CartView:
    cart_item = _get_cart_item(session, user_id, product_id)
    if not cart_item:
        raise NotFoundError("Item not found in cart")

    if cart_item.saved_for_later:
        cart_item.saved_for_later = False
        cart_item.updated_at = utcnow()
        session.commit()

    return get_cart(session, user_id)


def add_item(session: Session, user_id: int, product_id: int, quantity: int) -> CartView:
    if quantity < 1:
        raise InvalidInputError("Quantity must be at least 1")

    product = catalog.find_product(session, product_id)
    if not product:
        raise NotFoundError("Product not found")

    cart_item = _get_cart_item(session, user_id, product_id)
    if cart_item:
        cart_item.quantity += quantity
        cart_item.updated_at = utcnow()
        if cart_item.saved_for_later:
            cart_item.saved_for_later = False
        session.commit()
    else:
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            saved_for_later=False
        )
        session.add(cart_item)
        session.commit()

    return get_cart(session, user_id)


def update_quantity(session: Session, user_id: int, product_id: int, quantity: int) -> CartView:
    if quantity < 1:
        raise InvalidInputError("Quantity must be at least 1")

    cart_item = _get_cart_item(session, user_id, product_id)
    if not cart_item:
        raise NotFoundError("Item not found in cart")

    cart_item.quantity = quantity
    cart_item.updated_at = utcnow()
    session.commit()

    return get_cart(session, user_id)


def remove_item(session: Session, user_id: int, product_id: int) -> CartView:
    cart_item = _get_cart_item(session, user_id, product_id)
    if not cart_item:
        raise NotFoundError("Item not found in cart")

    session.delete(cart_item)
    session.commit()

    return get_cart(session, user_id)


def clear(session: Session, user_id: int) -> CartView:
    stmt = select(CartItem).where(CartItem.user_id == user_id)
    items = session.execute(stmt).scalars().all()
    for item in items:
        session.delete(item)
    session.commit()

    return CartView(user_id=user_id)
