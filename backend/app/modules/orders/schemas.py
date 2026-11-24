from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

from app.modules.orders.models import (
    OrderStatus, FulfillmentStatus, ShippingMethod, PaymentMethod
)

class OrderOut(BaseModel):
    id: int
    buyer_id: int
    status: OrderStatus
    fulfillment_status: FulfillmentStatus
    total_cents: int
    address: dict
    shipping_method: ShippingMethod
    payment_method: PaymentMethod
    items: List[dict]
    created_at: str
    paid_at: Optional[str]
    shipped_at: Optional[str]
    out_for_delivery_at: Optional[str]
    delivered_at: Optional[str]
    estimated_delivery_date: Optional[str]

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    seller_id: int
    quantity: int
    unit_price_cents: int
