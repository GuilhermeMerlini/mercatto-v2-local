from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint

from app.core import clock
from app.core.db import UTCDateTime


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
    __table_args__ = (UniqueConstraint("buyer_id", "idempotency_key"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(index=True)
    idempotency_key: Optional[str] = Field(default=None, max_length=255)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    fulfillment_status: FulfillmentStatus = Field(default=FulfillmentStatus.NOT_SHIPPED)
    total_cents: int = Field(gt=0)
    address_full_name: str = Field(max_length=255)
    address_street: str = Field(max_length=255)
    address_city: str = Field(max_length=255)
    address_state: str = Field(max_length=255)
    address_zip: str = Field(max_length=255)
    shipping_method: ShippingMethod = Field(default=ShippingMethod.STANDARD)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CARD)
    payment_transaction_id: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=clock.utcnow, sa_type=UTCDateTime)
    paid_at: Optional[datetime] = Field(default=None, sa_type=UTCDateTime)
    shipped_at: Optional[datetime] = Field(default=None, sa_type=UTCDateTime)
    out_for_delivery_at: Optional[datetime] = Field(default=None, sa_type=UTCDateTime)
    delivered_at: Optional[datetime] = Field(default=None, sa_type=UTCDateTime)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(index=True)
    product_id: int
    seller_id: int
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(gt=0)
