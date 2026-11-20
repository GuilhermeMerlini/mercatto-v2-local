"""Regras de negócio do módulo orders."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.errors import (
    InvalidInputError,
    NotFoundError,
)
from app.modules.catalog import service as catalog
from app.modules.orders import delivery
from app.modules.orders.models import (
    FulfillmentStatus,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    ShippingMethod,
)
from app.modules.payments import service as payments


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
    items: list[OrderItemView]
    created_at: datetime
    paid_at: Optional[datetime]
    shipped_at: Optional[datetime]
    out_for_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    estimated_delivery_date: Optional[date]


def checkout(
    session: Session,
    buyer_id: int,
    items: list[CheckoutItem],
    address: Address,
    shipping_method: ShippingMethod,
    payment_method: PaymentMethod,
    idempotency_key: Optional[str] = None,
) -> OrderView:
    # 1. Idempotência (chave vazia vale como sem chave)
    idempotency_key = idempotency_key or None
    if idempotency_key:
        stmt = select(Order).where(
            Order.buyer_id == buyer_id,
            Order.idempotency_key == idempotency_key,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            return _order_to_view(session, existing)

    # 2. Validação de entrada
    if not items:
        raise InvalidInputError("Items cannot be empty")

    # Agrupar itens por produto_id e validar
    item_map = {}
    for item in items:
        if item.quantity < 1:
            raise InvalidInputError("Quantity must be at least 1")
        if item.product_id in item_map:
            item_map[item.product_id] += item.quantity
        else:
            item_map[item.product_id] = item.quantity

    # Validar campos do endereço
    if not address.full_name.strip():
        raise InvalidInputError("Full name is required")
    if not address.street.strip():
        raise InvalidInputError("Street is required")
    if not address.city.strip():
        raise InvalidInputError("City is required")
    if not address.state.strip():
        raise InvalidInputError("State is required")
    if not address.zip.strip():
        raise InvalidInputError("Zip code is required")

    # Obter produtos
    product_views = catalog.get_many(session, list(item_map.keys()))
    product_dict = {p.id: p for p in product_views}
    if len(product_dict) != len(item_map):
        missing = set(item_map.keys()) - set(product_dict.keys())
        raise NotFoundError(f"Product(s) not found: {missing}")

    # 3. Reserva de estoque
    reserved = []
    try:
        for product_id, quantity in item_map.items():
            catalog.decrease_stock(session, product_id, quantity)
            reserved.append((product_id, quantity))
    except Exception:
        # Reverter todas as reservas
        for product_id, quantity in reserved:
            catalog.increase_stock(session, product_id, quantity)
        raise

    # 4. Criar pedido
    total_cents = 0
    order_items = []
    for product_id, quantity in item_map.items():
        product = product_dict[product_id]
        unit_price_cents = product.price_cents
        total_cents += unit_price_cents * quantity
        order_items.append(
            OrderItem(
                product_id=product_id,
                seller_id=product.seller_id,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
            )
        )

    order = Order(
        buyer_id=buyer_id,
        idempotency_key=idempotency_key,
        status=OrderStatus.PROCESSING,
        fulfillment_status=FulfillmentStatus.NOT_SHIPPED,
        total_cents=total_cents,
        address_full_name=address.full_name,
        address_street=address.street,
        address_city=address.city,
        address_state=address.state,
        address_zip=address.zip,
        shipping_method=shipping_method,
        payment_method=payment_method,
    )

    try:
        session.add(order)
        session.flush()  # Para obter o ID antes do commit
        order_id = order.id
    except IntegrityError:
        session.rollback()
        # Reverter todas as reservas
        for product_id, quantity in reserved:
            catalog.increase_stock(session, product_id, quantity)
        # Tentar novamente
        stmt = select(Order).where(
            Order.buyer_id == buyer_id,
            Order.idempotency_key == idempotency_key,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            return _order_to_view(session, existing)
        raise

    # Adicionar itens do pedido
    for item in order_items:
        item.order_id = order_id
    session.add_all(order_items)
    session.commit()

    # 5. Processar pagamento
    try:
        result = payments.charge(order_id, total_cents, "BRL")
    except Exception:
        # Marcar como FAILED e reverter estoque
        session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=OrderStatus.FAILED)
        )
        session.commit()
        # Reverter todas as reservas
        for product_id, quantity in reserved:
            catalog.increase_stock(session, product_id, quantity)
        raise

    # Atualizar status do pedido com base no resultado do pagamento
    if result.approved:
        session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                status=OrderStatus.PAID,
                paid_at=utcnow(),
                payment_transaction_id=result.transaction_id,
            )
        )
    else:
        # Pagamento recusado
        session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=OrderStatus.FAILED)
        )
        session.commit()
        # Reverter todas as reservas
        for product_id, quantity in reserved:
            catalog.increase_stock(session, product_id, quantity)
        # Não lançar exceção, apenas retornar o pedido como FAILED
        return _order_to_view(session, order)

    session.commit()
    return _order_to_view(session, order)


def _order_to_view(session: Session, order: Order) -> OrderView:
    # Obter itens do pedido
    stmt = select(OrderItem).where(OrderItem.order_id == order.id)
    items = session.execute(stmt).scalars().all()
    order_items = [
        OrderItemView(
            id=item.id,
            product_id=item.product_id,
            seller_id=item.seller_id,
            quantity=item.quantity,
            unit_price_cents=item.unit_price_cents,
        )
        for item in items
    ]

    # Criar endereço
    address = Address(
        full_name=order.address_full_name,
        street=order.address_street,
        city=order.address_city,
        state=order.address_state,
        zip=order.address_zip,
    )

    # Calcular data estimada de entrega
    estimated_delivery_date = delivery.estimate(order.paid_at or order.created_at, order.shipping_method)

    return OrderView(
        id=order.id,
        buyer_id=order.buyer_id,
        status=order.status,
        fulfillment_status=order.fulfillment_status,
        total_cents=order.total_cents,
        address=address,
        shipping_method=order.shipping_method,
        payment_method=order.payment_method,
        items=order_items,
        created_at=order.created_at,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        out_for_delivery_at=order.out_for_delivery_at,
        delivered_at=order.delivered_at,
        estimated_delivery_date=estimated_delivery_date,
    )
