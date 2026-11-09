"""Configuração lida do ambiente. Importada uma vez, na subida da app."""
import os

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mercatto.db")
# none (aprova tudo) | always (recusa tudo) | first-attempt (recusa a 1ª cobrança de cada pedido)
PAYMENT_MOCK_DECLINE = os.getenv("PAYMENT_MOCK_DECLINE", "none")
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]
