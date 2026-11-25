from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.deps import AuthUser, get_current_user
from app.modules.orders import service
from app.modules.orders.schemas import AddressIn, CheckoutIn, OrderOut, RetryPaymentIn

router = APIRouter(prefix="/api/orders")


@router.get("", response_model=list[OrderOut])
def list_orders(
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.list_by_buyer(session, auth.id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.get_order(session, order_id, auth.id)


@router.patch("/{order_id}/address", response_model=OrderOut)
def update_address(
    order_id: int,
    data: AddressIn,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    address = service.Address(
        full_name=data.full_name,
        street=data.street,
        city=data.city,
        state=data.state,
        zip=data.zip,
    )
    return service.update_shipping_address(session, order_id, auth.id, address)


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


@router.post("/{order_id}/payment", response_model=OrderOut)
def retry_payment(
    order_id: int,
    data: RetryPaymentIn,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.retry_payment(session, order_id, auth.id, data.payment_method)
