# tensalis/client.py
"""
Tensalis Python SDK - Official client for the Tensalis Hallucination Detection API.

This client provides a simple interface to verify LLM responses against source context,
detecting hallucinations, contradictions, and fabrications in real-time.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterator, List, Literal, Optional, Union

import requests

from .exceptions import TensalisAPIError, TensalisError, TensalisTimeoutError


class VerificationResult:
    """Represents the result of a verification request."""
    
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
    
    @property
    def status(self) -> Literal["VERIFIED", "BLOCKED", "WARNING"]:
        """Verification status: VERIFIED, BLOCKED, or WARNING."""
        return self._data.get("status", "VERIFIED")
    
    @property
    def severity(self) -> Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]]:
        """Severity level if blocked or warning."""
        return self._data.get("severity")
    
    @property
    def reason(self) -> Optional[str]:
        """Human-readable explanation of the issue."""
        return self._data.get("reason")
    
    @property
    def confidence(self) -> Optional[float]:
        """Confidence score (0.0 to 1.0) of the detection."""
        return self._data.get("confidence")
    
    @property
    def layer(self) -> Optional[str]:
        """Which detection layer triggered the block."""
        return self._data.get("layer")
    
    @property
    def latency_ms(self) -> Optional[int]:
        """Server-side processing time in milliseconds."""
        return self._data.get("latency_ms")
    
    @property
    def is_blocked(self) -> bool:
        """Returns True if the response was blocked."""
        return self.status == "BLOCKED"
    
    @property
    def is_verified(self) -> bool:
        """Returns True if the response passed verification."""
        return self.status == "VERIFIED"
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the raw response data as a dictionary."""
        return self._data.copy()
    
    def __repr__(self) -> str:
        return f"VerificationResult(status={self.status!r}, severity={self.severity!r})"


class TensalisClient:
    """
    Client for the Tensalis Hallucination Detection API.
    
    Args:
        api_key: Your Tensalis API key.
        endpoint: API endpoint URL. Defaults to production.
        timeout: Request timeout in seconds. Defaults to 30.
        retries: Number of retry attempts for failed requests. Defaults to 3.
        mode: Verification mode - "strict", "balanced", or "permissive".
    
    Example:
        >>> client = TensalisClient(api_key="your-api-key")
        >>> result = client.verify(
        ...     response="The policy allows 90-day returns.",
        ...     context=["Returns accepted within 30 days."]
        ... )
        >>> if result.is_blocked:
        ...     print(f"Blocked: {result.reason}")
    """
    
    DEFAULT_ENDPOINT = "https://api.tensalis.com/v1"
    VERSION = "0.1.0"
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 30,
        retries: int = 3,
        mode: Literal["strict", "balanced", "permissive"] = "balanced"
    ) -> None:
        if not api_key:
            raise TensalisError("API key is required")
        
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.mode = mode
        
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"tensalis-python/{self.VERSION}",
            "X-Tensalis-Mode": mode
        })
    
    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request with retries."""
        url = f"{self.endpoint}{path}"
        last_error: Optional[Exception] = None
        
        for attempt in range(self.retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", 1))
                    time.sleep(retry_after)
                    continue
                
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise TensalisAPIError(
                        message=error_data.get("error", "Unknown error"),
                        status_code=response.status_code,
                        response=error_data
                    )
                
                return response.json()
                
            except requests.Timeout as e:
                last_error = TensalisTimeoutError(f"Request timed out after {self.timeout}s")
            except requests.RequestException as e:
                last_error = TensalisError(f"Request failed: {e}")
            
            # Exponential backoff
            if attempt < self.retries - 1:
                time.sleep(2 ** attempt)
        
        raise last_error or TensalisError("Request failed after retries")
    
    def verify(
        self,
        response: str,
        context: Union[str, List[str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Verify an LLM response against source context.
        
        Args:
            response: The LLM-generated response to verify.
            context: Source context (string or list of strings).
            metadata: Optional metadata for logging/tracking.
        
        Returns:
            VerificationResult with status, severity, and details.
        
        Example:
            >>> result = client.verify(
            ...     response="The CEO is John Smith.",
            ...     context=["The CEO is Jane Doe."]
            ... )
            >>> print(result.status)  # "BLOCKED"
        """
        if isinstance(context, str):
            context = [context]
        
        payload = {
            "response": response,
            "reference_facts": context
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        data = self._request("POST", "/verify", payload)
        return VerificationResult(data)
    
    def verify_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[VerificationResult]:
        """
        Verify multiple responses in a single request.
        
        Args:
            items: List of dicts with "response" and "context" keys.
        
        Returns:
            List of VerificationResult objects.
        
        Example:
            >>> results = client.verify_batch([
            ...     {"response": "Answer 1", "context": ["Fact 1"]},
            ...     {"response": "Answer 2", "context": ["Fact 2"]},
            ... ])
        """
        payload = {"items": items}
        data = self._request("POST", "/verify/batch", payload)
        return [VerificationResult(r) for r in data.get("results", [])]
    
    def verify_stream(
        self,
        response_stream: Iterator[str],
        context: Union[str, List[str]],
        check_interval: int = 50
    ) -> Iterator[Dict[str, Any]]:
        """
        Verify a streaming response in real-time.
        
        Checks the accumulated response every `check_interval` tokens,
        allowing early termination when drift is detected.
        
        Args:
            response_stream: Iterator yielding response chunks.
            context: Source context for verification.
            check_interval: Tokens between verification checks.
        
        Yields:
            Dicts with "text" and "status" keys.
        
        Example:
            >>> for chunk in client.verify_stream(llm.stream(prompt), docs):
            ...     if chunk["status"] == "BLOCKED":
            ...         break
            ...     print(chunk["text"], end="")
        """
        if isinstance(context, str):
            context = [context]
        
        accumulated = ""
        token_count = 0
        
        for chunk in response_stream:
            accumulated += chunk
            token_count += len(chunk.split())
            
            if token_count >= check_interval:
                result = self.verify(response=accumulated, context=context)
                yield {
                    "text": chunk,
                    "status": result.status,
                    "result": result.to_dict() if result.is_blocked else None
                }
                
                if result.is_blocked:
                    return
                
                token_count = 0
            else:
                yield {"text": chunk, "status": "PENDING", "result": None}
    
    def health(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Dict with "status" and "latency_ms" keys.
        """
        return self._request("GET", "/health")
    
    def usage(self) -> Dict[str, Any]:
        """
        Get current usage statistics for your API key.
        
        Returns:
            Dict with usage metrics and limits.
        """
        return self._request("GET", "/usage")
    
    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()
    
    def __enter__(self) -> TensalisClient:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
