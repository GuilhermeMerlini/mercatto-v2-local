"""Serviço de pagamento."""
from app.core.config import PAYMENT_MOCK_DECLINE
from app.core.errors import InvalidInputError
from app.modules.payments import gateway


def charge(order_id: int, amount_cents: int, currency: str = "BRL") -> gateway.PaymentResult:
    """Cobra um valor de um pedido."""
    if amount_cents <= 0:
        raise InvalidInputError("Amount must be positive")
    return _gateway.charge(order_id, amount_cents, currency)


def set_gateway(gateway_: gateway.PaymentGateway) -> None:
    """Troca o gateway de pagamento."""
    global _gateway
    _gateway = gateway_


# Gateway inicial
_gateway = gateway.MockPaymentGateway(PAYMENT_MOCK_DECLINE)


# Reexportar tipos para outros módulos
PaymentResult = gateway.PaymentResult
PaymentGateway = gateway.PaymentGateway
MockPaymentGateway = gateway.MockPaymentGateway
