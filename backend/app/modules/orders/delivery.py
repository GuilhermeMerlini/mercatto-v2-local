from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.modules.orders.models import ShippingMethod


def estimate(start: datetime | None, method: ShippingMethod) -> date | None:
    if start is None:
        return None

    sp = start.astimezone(ZoneInfo("America/Sao_Paulo"))
    days = 1 if method == ShippingMethod.EXPRESS else 5

    # Calculate business days
    current = sp.date()
    added = 0
    while added < days:
        current += timedelta(days=1)
        weekday = current.weekday()
        if weekday < 5:  # Monday to Friday
            added += 1

    return current
