class DomainError(Exception):
    """Base exception for all domain errors."""


class MovimientoInvalidoError(DomainError):
    """Raised when a movimiento has invalid data."""


class CategoriaInexistenteError(DomainError):
    """Raised when a referenced category does not exist."""


class CuentaInexistenteError(DomainError):
    """Raised when a referenced bank account does not exist."""


class ValorInvalidoError(DomainError):
    """Raised when a monetary value is invalid (e.g. negative)."""
