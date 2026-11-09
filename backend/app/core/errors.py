"""Exceções de domínio. Services lançam estas; routers as traduzem para HTTP."""


class DomainError(Exception):
    """Base de todos os erros de negócio."""


class NotFoundError(DomainError):
    """Entidade não encontrada (HTTP 404)."""


class ConflictError(DomainError):
    """Conflito com o estado atual, ex.: email já cadastrado (HTTP 409)."""


class InsufficientStockError(DomainError):
    """Estoque insuficiente para a operação (HTTP 409)."""


class AuthenticationError(DomainError):
    """Credenciais inválidas (HTTP 401)."""
