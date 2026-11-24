from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.security import HTTPBearer, SecurityScopes

from app.core import deps
from app.core.db import get_session
from app.modules.orders import service
from app.modules.orders.schemas import OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_200_OK)
def checkout(
    session: Session = Depends(get_session),
    current_user: deps.AuthUser = Depends(deps.get_current_user),
    items: List[service.CheckoutItem] = Depends(),
    address: service.Address = Depends(),
    shipping_method: service.ShippingMethod = Depends(),
    payment_method: service.PaymentMethod = Depends(),
    idempotency_key: Optional[str] = None
):
    if current_user.role != "BUYER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyers can checkout")
    
    try:
        return service.checkout(session, current_user.id, items, address, shipping_method, payment_method, idempotency_key)
    except errors.InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except errors.NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except errors.InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
