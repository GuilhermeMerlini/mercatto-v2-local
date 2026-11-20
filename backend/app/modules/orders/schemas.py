from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.modules.orders.models import (
    FulfillmentStatus,
    OrderStatus,
    PaymentMethod,
    ShippingMethod,
)


class CheckoutItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class AddressIn(BaseModel):
    full_name: str
    street: str
    city: str
    state: str
    zip: str

    @field_validator("full_name", "street", "city", "state", "zip")
    @classmethod
    def not_empty_or_whitespace(cls, v: str, info: ValidationInfo) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")
        return v


class CheckoutIn(BaseModel):
    items: list[CheckoutItemIn] = Field(min_length=1)
    address: AddressIn
    shipping_method: ShippingMethod
    payment_method: PaymentMethod


class AddressOut(BaseModel):
    model_config = {"from_attributes": True}

    full_name: str
    street: str
    city: str
    state: str
    zip: str


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    seller_id: int
    quantity: int
    unit_price_cents: int


class OrderOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    buyer_id: int
    status: OrderStatus
    fulfillment_status: FulfillmentStatus
    total_cents: int
    address: AddressOut
    shipping_method: ShippingMethod
    payment_method: PaymentMethod
    items: list[OrderItemOut]
    created_at: datetime
    paid_at: Optional[datetime]
    shipped_at: Optional[datetime]
    out_for_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    estimated_delivery_date: Optional[date]
