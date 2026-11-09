import dataclasses
import threading

import pytest

from app.core.errors import InvalidInputError
from app.modules.payments import gateway as gw
from app.modules.payments import service


def test_payment_result_is_frozen_dataclass():
    result = gw.PaymentResult(True, "mock_1", "ok")
    assert dataclasses.is_dataclass(result)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.approved = False


def test_none_mode_approves_with_unique_ids():
    gateway = gw.MockPaymentGateway()
    results = [gateway.charge(order_id, 1000, "BRL") for order_id in (1, 1, 2)]
    assert all(r.approved for r in results)
    assert all(r.transaction_id.startswith("mock_") for r in results)
    assert len({r.transaction_id for r in results}) == 3


def test_always_mode_declines():
    result = gw.MockPaymentGateway("always").charge(1, 1000, "BRL")
    assert result.approved is False
    assert result.transaction_id is None
    assert result.message


def test_first_attempt_declines_once_per_order():
    gateway = gw.MockPaymentGateway("first-attempt")
    assert gateway.charge(1, 1000, "BRL").approved is False
    assert gateway.charge(1, 1000, "BRL").approved is True
    assert gateway.charge(1, 1000, "BRL").approved is True
    assert gateway.charge(2, 1000, "BRL").approved is False
    assert gateway.charge(2, 1000, "BRL").approved is True


def test_first_attempt_is_thread_safe():
    gateway = gw.MockPaymentGateway("first-attempt")
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(16)

    def charge():
        barrier.wait()
        r = gateway.charge(7, 1000, "BRL")
        with lock:
            results.append(r.approved)

    threads = [threading.Thread(target=charge) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(False) == 1


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        gw.MockPaymentGateway("sometimes")


class RecordingGateway:
    def __init__(self):
        self.calls = []

    def charge(self, order_id, amount_cents, currency):
        self.calls.append((order_id, amount_cents, currency))
        return gw.PaymentResult(True, "rec_1", "ok")


def test_service_delegates_to_current_gateway():
    recorder = RecordingGateway()
    service.set_gateway(recorder)
    result = service.charge(5, 2500)
    assert result.transaction_id == "rec_1"
    assert recorder.calls == [(5, 2500, "BRL")]
    service.charge(6, 100, "USD")
    assert recorder.calls[-1] == (6, 100, "USD")


@pytest.mark.parametrize("amount", [0, -100])
def test_service_rejects_non_positive_amount(amount):
    with pytest.raises(InvalidInputError):
        service.charge(1, amount)


def test_initial_gateway_comes_from_config(monkeypatch):
    import importlib

    from app.core import config

    monkeypatch.setattr(config, "PAYMENT_MOCK_DECLINE", "always")
    try:
        importlib.reload(service)
        assert service.charge(1, 100).approved is False
    finally:
        monkeypatch.setattr(config, "PAYMENT_MOCK_DECLINE", "none")
        importlib.reload(service)
    assert service.charge(1, 100).approved is True


def test_service_reexports_types():
    assert service.PaymentResult is gw.PaymentResult
    assert service.MockPaymentGateway is gw.MockPaymentGateway
    assert service.PaymentGateway is gw.PaymentGateway


def test_payments_depends_on_nothing():
    from pathlib import Path

    folder = Path(gw.__file__).parent
    for f in folder.glob("*.py"):
        source = f.read_text()
        for other in ("users", "catalog", "search", "cart", "orders", "reviews", "sellers"):
            assert f"app.modules.{other}" not in source, f"{f.name} importa {other}"
