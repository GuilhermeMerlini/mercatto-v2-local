from datetime import datetime, timezone


def utcnow() -> datetime:
    """Data/hora atual em UTC, com tzinfo. Todas as datas do sistema são UTC."""
    return datetime.now(timezone.utc)
