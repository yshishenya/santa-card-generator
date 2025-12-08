"""Service layer exceptions for the card generation service.

This module defines the exception hierarchy for card generation operations,
providing specific error types for different failure scenarios.
"""


class CardServiceError(Exception):
    """Base exception for all card service errors.

    All custom exceptions in the card service should inherit from this class
    to allow for easy exception handling at the API layer.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with an error message.

        Args:
            message: Descriptive error message.
        """
        self.message = message
        super().__init__(self.message)


class RecipientNotFoundError(CardServiceError):
    """Raised when the specified recipient is not found in the employee list.

    This error indicates that the employee name provided in the card generation
    request does not match any employee in the system.
    """

    def __init__(self, employee_name: str) -> None:
        """Initialize with the employee name that was not found.

        Args:
            employee_name: The name of the employee that could not be found.
        """
        self.employee_name = employee_name
        super().__init__(f"Employee not found: {employee_name}")


class SessionNotFoundError(CardServiceError):
    """Raised when a session ID is not found in the session manager.

    This error indicates that the provided session ID does not correspond to
    any active generation session.
    """

    def __init__(self, session_id: str) -> None:
        """Initialize with the session ID that was not found.

        Args:
            session_id: The session ID that could not be found.
        """
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionExpiredError(CardServiceError):
    """Raised when attempting to use an expired session.

    This error indicates that the session existed but has expired due to
    exceeding the TTL (time-to-live) threshold.
    """

    def __init__(self, session_id: str) -> None:
        """Initialize with the expired session ID.

        Args:
            session_id: The session ID that has expired.
        """
        self.session_id = session_id
        super().__init__(f"Session expired: {session_id}")


class RegenerationLimitExceededError(CardServiceError):
    """Raised when the regeneration limit has been exceeded.

    This error indicates that the maximum number of regeneration attempts
    for either text or images has been reached for the current session.
    """

    def __init__(self, element_type: str, max_regenerations: int) -> None:
        """Initialize with the element type and regeneration limit.

        Args:
            element_type: Type of element ('text' or 'image').
            max_regenerations: Maximum number of regenerations allowed.
        """
        self.element_type = element_type
        self.max_regenerations = max_regenerations
        super().__init__(
            f"Regeneration limit exceeded for {element_type}: "
            f"maximum {max_regenerations} regenerations allowed"
        )


class VariantNotFoundError(CardServiceError):
    """Raised when a requested variant (text or image) is not found.

    This error indicates that the specified variant index does not exist
    in the session's variant list.
    """

    def __init__(self, element_type: str, variant_index: int) -> None:
        """Initialize with the element type and variant index.

        Args:
            element_type: Type of element ('text' or 'image').
            variant_index: Index of the variant that was not found.
        """
        self.element_type = element_type
        self.variant_index = variant_index
        super().__init__(f"{element_type.capitalize()} variant not found at index: {variant_index}")
