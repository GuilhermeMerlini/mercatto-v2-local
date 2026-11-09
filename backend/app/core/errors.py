"""Exceções de domínio. Services lançam estas; `main.py` as traduz para HTTP."""


class DomainError(Exception):
    """Base de todos os erros de negócio. Status HTTP em `status_code`."""

    status_code = 400

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message or self.__class__.__name__


class InvalidInputError(DomainError):
    """Entrada inválida para a regra de negócio (HTTP 400)."""

    status_code = 400


class AuthenticationError(DomainError):
    """Credenciais ou token inválidos (HTTP 401)."""

    status_code = 401


class ForbiddenError(DomainError):
    """Usuário autenticado sem permissão para a operação (HTTP 403)."""

    status_code = 403


class NotFoundError(DomainError):
    """Entidade não encontrada (HTTP 404)."""

    status_code = 404


class ConflictError(DomainError):
    """Conflito com o estado atual, ex.: email já cadastrado (HTTP 409)."""

    status_code = 409


class InsufficientStockError(ConflictError):
    """Estoque insuficiente para a operação (HTTP 409)."""
