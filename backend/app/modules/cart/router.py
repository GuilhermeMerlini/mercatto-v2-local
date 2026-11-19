from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.deps import AuthUser, get_current_user
from app.modules.cart import service
from app.modules.cart.schemas import CartItemIn, CartItemUpdate

router = APIRouter(prefix="/api/cart")


@router.get("/{user_id}", response_model=service.CartView)
def get_cart(
    user_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.get_cart(session, user_id)


@router.delete("/{user_id}", response_model=service.CartView)
def clear_cart(
    user_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.clear(session, user_id)


@router.post("/{user_id}/items", response_model=service.CartView)
def add_item(
    user_id: int,
    data: CartItemIn,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.add_item(session, user_id, data.product_id, data.quantity)


@router.put("/{user_id}/items/{product_id}", response_model=service.CartView)
def update_quantity(
    user_id: int,
    product_id: int,
    data: CartItemUpdate,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.update_quantity(session, user_id, product_id, data.quantity)


@router.delete("/{user_id}/items/{product_id}", response_model=service.CartView)
def remove_item(
    user_id: int,
    product_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.remove_item(session, user_id, product_id)


@router.post("/{user_id}/items/{product_id}/save-for-later", response_model=service.CartView)
def save_for_later(
    user_id: int,
    product_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.save_for_later(session, user_id, product_id)


@router.post("/{user_id}/items/{product_id}/move-to-cart", response_model=service.CartView)
def move_to_cart(
    user_id: int,
    product_id: int,
    auth: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    auth.require_owner(user_id)
    return service.move_to_cart(session, user_id, product_id)
