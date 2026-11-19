from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.deps import AuthUser, get_current_user
from app.core.pagination import Page
from app.modules.catalog import service
from app.modules.catalog.schemas import ProductIn, ProductOut

router = APIRouter(prefix="/api/catalog")

@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=ProductOut)
def create_product(
    data: ProductIn,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.require_role("SELLER")
    product_data = service.ProductData(
        name=data.name,
        price_cents=data.price_cents,
        stock=data.stock,
        category=data.category,
        description=data.description,
        image_url=data.image_url,
        brand=data.brand,
        warranty_months=data.warranty_months,
        model_number=data.model_number,
        list_price_cents=data.list_price_cents,
    )
    return service.create_product(session, current_user.id, product_data)


@router.get("/products", response_model=Page[ProductOut])
def list_products(
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    items, total = service.list_products(session, category, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=list[str])
def list_categories(
    session: Session = Depends(get_session),
):
    return service.list_categories(session)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    return service.get_product(session, product_id)


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductIn,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.require_role("SELLER")
    product_data = service.ProductData(
        name=data.name,
        price_cents=data.price_cents,
        stock=data.stock,
        category=data.category,
        description=data.description,
        image_url=data.image_url,
        brand=data.brand,
        warranty_months=data.warranty_months,
        model_number=data.model_number,
        list_price_cents=data.list_price_cents,
    )
    return service.update_product(session, product_id, current_user.id, product_data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.require_role("SELLER")
    service.delete_product(session, product_id, current_user.id)
