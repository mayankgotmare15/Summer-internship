"""Domain exception hierarchy and standard error response schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Standard error response payload across all 4xx/5xx responses."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    request_id: str = ""


class DomainError(Exception):
    """Base exception for all domain and business rule violations."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field
        self.details = details or {}


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found", field: Optional[str] = None):
        super().__init__(message, code="NOT_FOUND", status_code=404, field=field)


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "Authentication required", code: str = "AUTH_REQUIRED"):
        super().__init__(message, code=code, status_code=401)


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Action forbidden for caller role", code: str = "FORBIDDEN_ROLE"):
        super().__init__(message, code=code, status_code=403)


class InvalidTransitionError(DomainError):
    def __init__(self, message: str = "Invalid ticket status transition"):
        super().__init__(message, code="INVALID_TRANSITION", status_code=409)


class StaleVersionError(DomainError):
    def __init__(self, message: str = "Resource modified concurrently. Please refetch."):
        super().__init__(message, code="STALE_VERSION", status_code=409)


class EscalationGuardrailError(DomainError):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=code, status_code=422, details=details)


class ModelUnavailableError(DomainError):
    def __init__(self, message: str = "Inference model is currently unavailable"):
        super().__init__(message, code="MODEL_UNAVAILABLE", status_code=503)
