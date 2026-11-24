from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.deps import AuthUser, get_current_user
from app.modules.orders import service
from app.modules.orders.schemas import CheckoutIn, OrderOut

router = APIRouter(prefix="/api/orders")


@router.post("/checkout", response_model=OrderOut)
def checkout(
    data: CheckoutIn,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_role("BUYER")
    checkout_items = [
        service.CheckoutItem(item.product_id, item.quantity)
        for item in data.items
    ]
    address = service.Address(
        full_name=data.address.full_name,
        street=data.address.street,
        city=data.address.city,
        state=data.address.state,
        zip=data.address.zip,
    )
    return service.checkout(
        session,
        buyer_id=auth.id,
        items=checkout_items,
        address=address,
        shipping_method=data.shipping_method,
        payment_method=data.payment_method,
        idempotency_key=idempotency_key,
    )
