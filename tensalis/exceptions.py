# tensalis/exceptions.py
"""
Tensalis SDK Exception Classes.

This module defines the exception hierarchy for the Tensalis Python SDK.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class TensalisError(Exception):
    """
    Base exception for all Tensalis SDK errors.
    
    Attributes:
        message: Human-readable error description.
    """
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return self.message


class TensalisAPIError(TensalisError):
    """
    Exception raised when the Tensalis API returns an error response.
    
    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code from the API.
        response: Full error response from the API.
    
    Example:
        >>> try:
        ...     result = client.verify(response="...", context=["..."])
        ... except TensalisAPIError as e:
        ...     print(f"API Error {e.status_code}: {e.message}")
    """
    
    def __init__(
        self,
        message: str,
        status_code: int,
        response: Optional[Dict[str, Any]] = None
    ) -> None:
        self.status_code = status_code
        self.response = response or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return f"[{self.status_code}] {self.message}"
    
    @property
    def error_code(self) -> Optional[str]:
        """Return the API error code if available."""
        return self.response.get("code")
    
    @property
    def request_id(self) -> Optional[str]:
        """Return the request ID for debugging."""
        return self.response.get("request_id")


class TensalisAuthenticationError(TensalisAPIError):
    """
    Exception raised when authentication fails.
    
    This typically occurs when:
    - API key is invalid or expired
    - API key lacks required permissions
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        response: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=401, response=response)


class TensalisRateLimitError(TensalisAPIError):
    """
    Exception raised when rate limits are exceeded.
    
    Attributes:
        retry_after: Seconds to wait before retrying.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        response: Optional[Dict[str, Any]] = None
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429, response=response)
    
    def __str__(self) -> str:
        return f"{self.message} (retry after {self.retry_after}s)"


class TensalisTimeoutError(TensalisError):
    """
    Exception raised when a request times out.
    """
    pass


class TensalisValidationError(TensalisError):
    """
    Exception raised when input validation fails.
    
    This occurs client-side before making an API request.
    
    Attributes:
        field: The field that failed validation.
        details: Additional validation details.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.field = field
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.field:
            return f"Validation error on '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class TensalisConnectionError(TensalisError):
    """
    Exception raised when connection to the API fails.
    
    This may occur due to:
    - Network connectivity issues
    - DNS resolution failures
    - API endpoint unavailability
    """
    pass
