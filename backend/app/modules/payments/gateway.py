"""Gateway de pagamento mock."""
import threading
import uuid
from dataclasses import dataclass
from typing import Protocol, Set


@dataclass(frozen=True)
class PaymentResult:
    """Resultado de uma operação de pagamento."""

    approved: bool
    transaction_id: str | None
    message: str


class PaymentGateway(Protocol):
    """Protocolo para gateways de pagamento."""

    def charge(self, order_id: int, amount_cents: int, currency: str) -> PaymentResult:
        """Cobra um valor de um pedido."""


class MockPaymentGateway:
    """Gateway de pagamento mock."""

    def __init__(self, decline_mode: str = "none"):
        if decline_mode not in ("none", "always", "first-attempt"):
            raise ValueError("Invalid decline mode")
        self._decline_mode = decline_mode
        self._declined_orders: Set[int] = set()
        self._lock = threading.Lock()

    def charge(self, order_id: int, amount_cents: int, currency: str) -> PaymentResult:
        """Cobra um valor de um pedido."""
        if self._decline_mode == "always":
            return PaymentResult(False, None, "Payment declined by mock gateway")
        if self._decline_mode == "first-attempt":
            with self._lock:
                if order_id in self._declined_orders:
                    approved = True
                    transaction_id = None
                else:
                    self._declined_orders.add(order_id)
                    approved = False
                    transaction_id = None
        else:
            approved = True
            transaction_id = None

        if approved:
            transaction_id = f"mock_{uuid.uuid4().hex}"

        return PaymentResult(
            approved=approved,
            transaction_id=transaction_id,
            message="Payment processed successfully" if approved else "Payment declined by mock gateway"
        )
