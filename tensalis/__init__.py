# tensalis/__init__.py
"""
Tensalis Python SDK - Official client for the Tensalis Hallucination Detection API.

Basic usage:
    >>> from tensalis import TensalisClient
    >>> client = TensalisClient(api_key="your-api-key")
    >>> result = client.verify(
    ...     response="The policy allows 90-day returns.",
    ...     context=["Returns accepted within 30 days."]
    ... )
    >>> if result.is_blocked:
    ...     print(f"Hallucination detected: {result.reason}")

For more information, see: https://docs.tensalis.com
"""

from .client import TensalisClient, VerificationResult
from .exceptions import (
    TensalisError,
    TensalisAPIError,
    TensalisAuthenticationError,
    TensalisRateLimitError,
    TensalisTimeoutError,
    TensalisValidationError,
    TensalisConnectionError,
)

__version__ = "0.1.0"
__author__ = "Tensalis AI Ltd"
__email__ = "engineering@tensalis.com"

__all__ = [
    # Client
    "TensalisClient",
    "VerificationResult",
    # Exceptions
    "TensalisError",
    "TensalisAPIError",
    "TensalisAuthenticationError",
    "TensalisRateLimitError",
    "TensalisTimeoutError",
    "TensalisValidationError",
    "TensalisConnectionError",
    # Metadata
    "__version__",
]
