"""Shared domain exceptions matching Engineer 1's design contract."""


class CampusFlowError(Exception):
    """Base exception for all CampusFlow domain errors."""


class ValidationError(CampusFlowError):
    """Raised when user input fails domain validation rules."""


class TicketNotFoundError(CampusFlowError):
    """Raised when a ticket cannot be found by its identifier."""


class InvalidTransitionError(CampusFlowError):
    """Raised when an invalid status transition is attempted."""


class StorageError(CampusFlowError):
    """Raised when ticket persistence fails or storage is corrupted."""
