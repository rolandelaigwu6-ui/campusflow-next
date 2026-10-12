"""Domain exceptions for CampusFlow."""


class CampusFlowError(Exception):
    """Base exception for all CampusFlow domain errors."""
    pass


class ValidationError(CampusFlowError):
    """Raised when user input fails domain validation rules."""
    pass


class TicketNotFoundError(CampusFlowError):
    """Raised when a ticket cannot be found by its identifier."""
    pass


class InvalidTransitionError(CampusFlowError):
    """Raised when an invalid status transition is attempted."""
    pass


class StorageError(CampusFlowError):
    """Raised when ticket persistence fails or storage is corrupted."""
    pass
