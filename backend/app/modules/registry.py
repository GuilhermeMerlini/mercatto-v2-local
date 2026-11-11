"""Arquivo que só importa os `models.py` dos módulos, para o `SQLModel.metadata` conhecer as tabelas."""

from app.modules.users.models import User  # noqa: F401
