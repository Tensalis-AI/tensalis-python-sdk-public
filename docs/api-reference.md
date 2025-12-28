# Tensalis API Reference

## TensalisClient

The main client for interacting with the Tensalis Hallucination Detection API.

### Constructor

```python
TensalisClient(
    api_key: str,
    endpoint: str = "https://api.tensalis.com/v1",
    timeout: int = 30,
    retries: int = 3,
    mode: Literal["strict", "balanced", "permissive"] = "balanced"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | Your Tensalis API key |
| `endpoint` | `str` | `https://api.tensalis.com/v1` | API endpoint URL |
| `timeout` | `int` | `30` | Request timeout in seconds |
| `retries` | `int` | `3` | Number of retry attempts |
| `mode` | `str` | `"balanced"` | Verification strictness |

**Modes:**

- `strict`: Block on any uncertainty (recommended for healthcare, legal, finance)
- `balanced`: Block on high-confidence issues (general enterprise use)
- `permissive`: Block only clear contradictions (creative applications)

---

## Methods

### verify()

Verify an LLM response against source context.

```python
verify(
    response: str,
    context: Union[str, List[str]],
    metadata: Optional[Dict[str, Any]] = None
) -> VerificationResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `response` | `str` | The LLM-generated response to verify |
| `context` | `str` or `List[str]` | Source context / reference facts |
| `metadata` | `Dict` (optional) | Custom metadata for logging |

**Returns:** `VerificationResult`

**Example:**

```python
result = client.verify(
    response="The medication should be taken twice daily.",
    context=["Take one tablet daily with food."]
)

if result.is_blocked:
    print(f"Hallucination: {result.reason}")
```

---

### verify_batch()

Verify multiple responses in a single request.

```python
verify_batch(
    items: List[Dict[str, Any]]
) -> List[VerificationResult]
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `List[Dict]` | List of `{"response": ..., "context": ...}` dicts |

**Returns:** `List[VerificationResult]`

**Example:**

```python
results = client.verify_batch([
    {"response": "Answer 1", "context": ["Fact 1", "Fact 2"]},
    {"response": "Answer 2", "context": ["Fact 3"]},
])

for i, result in enumerate(results):
    print(f"Item {i}: {result.status}")
```

---

### verify_stream()

Verify a streaming response in real-time.

```python
verify_stream(
    response_stream: Iterator[str],
    context: Union[str, List[str]],
    check_interval: int = 50
) -> Iterator[Dict[str, Any]]
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_stream` | `Iterator[str]` | Iterator yielding response chunks |
| `context` | `str` or `List[str]` | Source context |
| `check_interval` | `int` | Tokens between verification checks |

**Yields:** `Dict` with keys: `text`, `status`, `result`

**Example:**

```python
for chunk in client.verify_stream(llm.stream(prompt), docs):
    if chunk["status"] == "BLOCKED":
        print("Drift detected, stopping generation")
        break
    print(chunk["text"], end="")
```

---

### health()

Check API health status.

```python
health() -> Dict[str, Any]
```

**Returns:**

```python
{
    "status": "healthy",
    "latency_ms": 2,
    "version": "1.0.0"
}
```

---

### usage()

Get usage statistics for your API key.

```python
usage() -> Dict[str, Any]
```

**Returns:**

```python
{
    "requests_today": 1523,
    "requests_this_month": 45000,
    "limit_daily": 10000,
    "limit_monthly": 500000,
    "plan": "enterprise"
}
```

---

## VerificationResult

Represents the result of a verification request.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `status` | `str` | `"VERIFIED"`, `"BLOCKED"`, or `"WARNING"` |
| `severity` | `str` or `None` | `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"` |
| `reason` | `str` or `None` | Human-readable explanation |
| `confidence` | `float` or `None` | Detection confidence (0.0-1.0) |
| `layer` | `str` or `None` | Which layer triggered the block |
| `latency_ms` | `int` or `None` | Processing time in milliseconds |
| `is_blocked` | `bool` | `True` if status is BLOCKED |
| `is_verified` | `bool` | `True` if status is VERIFIED |

### Methods

```python
to_dict() -> Dict[str, Any]  # Return raw response data
```

---

## Exceptions

### TensalisError

Base exception for all SDK errors.

```python
class TensalisError(Exception):
    message: str
```

### TensalisAPIError

Raised when the API returns an error.

```python
class TensalisAPIError(TensalisError):
    status_code: int
    response: Dict[str, Any]
    error_code: Optional[str]
    request_id: Optional[str]
```

### TensalisAuthenticationError

Raised when authentication fails (401).

### TensalisRateLimitError

Raised when rate limits are exceeded (429).

```python
class TensalisRateLimitError(TensalisAPIError):
    retry_after: int  # Seconds to wait
```

### TensalisTimeoutError

Raised when a request times out.

### TensalisValidationError

Raised for client-side validation errors.

```python
class TensalisValidationError(TensalisError):
    field: Optional[str]
    details: Dict[str, Any]
```

---

## Response Status Codes

| Status | Description | Action |
|--------|-------------|--------|
| `VERIFIED` | Response is consistent with context | Safe to use |
| `BLOCKED` | Hallucination detected | Do not use, regenerate |
| `WARNING` | Potential issues detected | Review before use |

---

## Detection Layers

When a response is blocked, the `layer` property indicates which detection mechanism triggered:

| Layer | Description |
|-------|-------------|
| `redshift_fidelity` | Off-topic semantic drift detected |
| `cascading_nli` | Logical contradiction with source facts |
| `blueshift_fidelity` | Information fabrication / expansion |
| `claim_verification` | Specific factual claim mismatch |

---

## Rate Limits

| Plan | Requests/Day | Requests/Month |
|------|--------------|----------------|
| Free | 100 | 1,000 |
| Starter | 1,000 | 25,000 |
| Pro | 10,000 | 250,000 |
| Enterprise | Custom | Custom |

Rate limit headers are included in all responses:

- `X-RateLimit-Limit`: Your daily limit
- `X-RateLimit-Remaining`: Remaining requests today
- `X-RateLimit-Reset`: Unix timestamp when limit resets
