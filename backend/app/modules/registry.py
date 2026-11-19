"""Arquivo que só importa os `models.py` dos módulos, para o `SQLModel.metadata` conhecer as tabelas."""

from app.modules.cart.models import CartItem  # noqa: F401
from app.modules.catalog.models import Product  # noqa: F401
from app.modules.users.models import User  # noqa: F401
