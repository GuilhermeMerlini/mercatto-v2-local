from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from app.core import clock, errors
from app.core.db import get_session
from app.modules.catalog.service import decrease_stock, increase_stock, get_product
from app.modules.payments.service import charge
from app.modules.orders import models, delivery
from app.modules.orders.models import Order, OrderItem, OrderStatus, FulfillmentStatus, ShippingMethod, PaymentMethod
from app.core.deps import get_current_user, AuthUser
from datetime import date

@dataclass(frozen=True)
class Address:
    full_name: str
    street: str
    city: str
    state: str
    zip: str

@dataclass(frozen=True)
class CheckoutItem:
    product_id: int
    quantity: int

@dataclass(frozen=True)
class OrderItemView:
    id: int
    product_id: int
    seller_id: int
    quantity: int
    unit_price_cents: int

@dataclass(frozen=True)
class OrderView:
    id: int
    buyer_id: int
    status: OrderStatus
    fulfillment_status: FulfillmentStatus
    total_cents: int
    address: Address
    shipping_method: ShippingMethod
    payment_method: PaymentMethod
    items: List[OrderItemView]
    created_at: datetime
    paid_at: Optional[datetime]
    shipped_at: Optional[datetime]
    out_for_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    estimated_delivery_date: Optional[date]

def checkout(
    session: Session,
    buyer_id: int,
    items: List[CheckoutItem],
    address: Address,
    shipping_method: ShippingMethod,
    payment_method: PaymentMethod,
    idempotency_key: Optional[str] = None
) -> OrderView:
    if idempotency_key:
        existing = session.execute(
            select(models.Order).where(
                models.Order.buyer_id == buyer_id,
                models.Order.idempotency_key == idempotency_key
            )
        ).scalar_one_or_none()
        if existing:
            return OrderView(**existing.__dict__)
    
    if not items or any(i.quantity < 1 for i in items):
        raise errors.InvalidInputError("Items must have quantity >= 1")
    
    product_ids = [i.product_id for i in items]
    products = session.execute(
        select(models.Product).where(models.Product.id.in_(product_ids))
    ).scalars().all()
    
    product_map = {p.id: p for p in products}
    missing = [pid for pid in product_ids if pid not in product_map]
    if missing:
        raise errors.NotFoundError(f"Product(s) {missing} not found")
    
    try:
        for item in items:
            product = product_map[item.product_id]
            decrease_stock(session, product.id, item.quantity)
    except errors.InsufficientStockError as e:
        for item in items:
            product = product_map[item.product_id]
            increase_stock(session, product.id, item.quantity)
        raise e
    
    order = models.Order(
        buyer_id=buyer_id,
        idempotency_key=idempotency_key,
        status=OrderStatus.PROCESSING,
        fulfillment_status=FulfillmentStatus.NOT_SHIPPED,
        shipping_method=shipping_method,
        payment_method=payment_method,
        address_full_name=address.full_name,
        address_street=address.street,
        address_city=address.city,
        address_state=address.state,
        address_zip=address.zip
    )
    session.add(order)
    session.flush()
    
    order_items = []
    total_cents = 0
    for item in items:
        product = product_map[item.product_id]
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            seller_id=product.seller_id,
            quantity=item.quantity,
            unit_price_cents=product.price_cents
        )
        order_items.append(order_item)
        total_cents += product.price_cents * item.quantity
    
    order.total_cents = total_cents
    session.add_all(order_items)
    session.flush()
    
    try:
        result = charge(order.id, total_cents, "BRL")
        if result.approved:
            order.status = OrderStatus.PAID
            order.paid_at = clock.utcnow()
            order.payment_transaction_id = result.transaction_id
        else:
            order.status = OrderStatus.FAILED
            order.paid_at = None
            order.payment_transaction_id = None
    except Exception:
        order.status = OrderStatus.FAILED
        order.paid_at = None
        order.payment_transaction
        raise
    
    session.commit()
    session.expire_all()
    
    items = [
        OrderItemView(
            id=item.id,
            product_id=item.product_id,
            seller_id=item.seller_id,
            quantity=item.quantity,
            unit_price_cents=item.unit_price_cents
        ) for item in order_items
    ]
    
    estimated_date = delivery.estimate(order.paid_at or order.created_at, shipping_method)
    return OrderView(
        id=order.id,
        buyer_id=order.buyer_id,
        status=order.status,
        fulfillment_status=order.fulfillment_status,
        total_cents=order.total_cents,
        address=address,
        shipping_method=shipping_method,
        payment_method=payment_method,
        items=items,
        created_at=order.created_at,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        out_for_delivery_at=order.out_for_delivery_at,
        delivered_at=order.delivered_at,
        estimated_delivery_date=estimated_date
    )
