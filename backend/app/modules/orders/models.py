from enum import Enum
from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Relationship
from app.core import clock
from sqlmodel import Relationship

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class FulfillmentStatus(str, Enum):
    NOT_SHIPPED = "NOT_SHIPPED"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"

class ShippingMethod(str, Enum):
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    PICKUP = "PICKUP"

class PaymentMethod(str, Enum):
    CARD = "CARD"
    STORE = "STORE"
    GIFT = "GIFT"

class Order(SQLModel, table=True):
    __tablename__ = "order"
    id: int = Field(default=None, primary_key=True)
    buyer_id: int = Field(index=True)
    idempotency_key: Optional[str] = Field(default=None, unique=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    fulfillment_status: FulfillmentStatus = Field(default=FulfillmentStatus.NOT_SHIPPED)
    total_cents: int = Field(default=0)
    address_full_name: str = Field()
    address_street: str = Field()
    address_city: str = Field()
    address_state: str = Field()
    address_zip: str = Field()
    shipping_method: ShippingMethod = Field()
    payment_method: PaymentMethod = Field()
    payment_transaction_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=clock.utcnow)
    paid_at: Optional[datetime] = Field(default=None)
    shipped_at: Optional[datetime] = Field(default=None)
    out_for_delivery_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    items: List[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "select"})

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_item"
    id: int = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(index=True)
    seller_id: int = Field(index=True)
    quantity: int = Field(default=1)
    unit_price_cents: int = Field(default=0)
    order: Order = Relationship(back_populates="items", sa_relationship_kwargs={"lazy": "select"})

