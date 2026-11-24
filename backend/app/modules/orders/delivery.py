from datetime import datetime, timedelta, date
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

class ShippingMethod(Enum):
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    PICKUP = "PICKUP"

def estimate(start: Optional[datetime], method: ShippingMethod) -> Optional[date]:
    if start is None:
        return None
    
    sao_paulo = ZoneInfo("America/Sao_Paulo")
    start = start.replace(tzinfo=sao_paulo)
    
    days = 1 if method == ShippingMethod.EXPRESS else 5
    business_days = 0
    current = start
    
    while business_days < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            business_days += 1
    
    return current.date()
