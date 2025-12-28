# Tensalis AI - Python Client

[![Build Status](https://github.com/tensalis-ai/tensalis-python-sdk/workflows/CI/badge.svg)](https://github.com/tensalis-ai/tensalis-python-sdk/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

The official Python client for the **Tensalis Hallucination Detection Engine**.

Tensalis provides a real-time safety layer for Enterprise RAG applications. It uses a proprietary **Kinematic Drift Detection** engine (Patent Pending) to quantify the velocity and acceleration of semantic drift in LLM responses.

---

## Architecture Overview

Tensalis uses a multi-layer verification architecture to catch hallucinations that single-method approaches miss:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TENSALIS VERIFICATION ENGINE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Layer 1   │    │   Layer 2   │    │   Layer 3   │         │
│  │  Redshift   │───▶│  Cascading  │───▶│  Blueshift  │         │
│  │  Fidelity   │    │     NLI     │    │  Fidelity   │         │
│  │  (Drift)    │    │ (Inference) │    │(Fabrication)│         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Semantic Gyroscope (Auto-Correction)           ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                  │
│                              ▼                                  │
│                    [ VERIFIED | BLOCKED ]                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Why Multi-Layer?**
- **Redshift** catches off-topic drift (high similarity, wrong direction)
- **Cascading NLI** catches logical contradictions (89%+ similarity but factually wrong)
- **Blueshift** catches fabrications (information density expansion)

No single layer catches all hallucination types. Our research shows 23% of hallucinations pass embedding-only checks.

---

## Features

* **Real-time Verification:** Sub-10ms latency for 80% of claims via our Cascading Inference architecture.
* **Kinematic Drift Monitoring:** Detects "hallucination acceleration" before the model finishes generating.
* **Fabrication Detection:** Distinguishes between "Redshift" (off-topic drift) and "Blueshift" (information expansion/fabrication).
* **Auto-Correction:** Automatically truncates and regenerates responses when drift is detected.

---

## Performance (Preliminary)

Early internal testing shows significant improvements over single-layer approaches:

| Metric | Tensalis | Embedding-Only | NLI-Only |
|--------|----------|----------------|----------|
| Precision | ~94% | ~78% | ~86% |
| Recall | ~92% | ~71% | ~83% |
| F1 Score | ~93% | ~75% | ~85% |
| Latency (p50) | <10ms | ~3ms | ~45ms |
| Latency (p99) | <50ms | ~12ms | ~180ms |

> ⚠️ **Note:** These are preliminary results from internal testing. Independent benchmarks on HaluEval, TruthfulQA, and other standard datasets are in progress. We will publish formal evaluation results soon.

---

## Installation

### From GitHub (Current)

```bash
# Install directly from GitHub
pip install git+https://github.com/tensalis-ai/tensalis-python-sdk.git

# Or clone and install locally
git clone https://github.com/tensalis-ai/tensalis-python-sdk.git
cd tensalis-python-sdk
pip install -e .
```

### From PyPI (Coming Soon)

```bash
# Not yet available - coming soon
pip install tensalis
```

---

## Quick Start

```python
from tensalis import TensalisClient

# Initialize with your API Key
client = TensalisClient(api_key="YOUR_API_KEY")

# Verify a RAG Response
result = client.verify(
    response="The refund policy allows returns within 90 days.",
    context=["Returns are accepted within 30 days of purchase."]
)

if result["status"] == "BLOCKED":
    print(f"Hallucination detected! Severity: {result['severity']}")
    print(f"Reason: {result['reason']}")
else:
    print("Response validated.")
```

---

## Detailed Usage

### Basic Verification

```python
from tensalis import TensalisClient

client = TensalisClient(api_key="your-api-key")

result = client.verify(
    response="The medication should be taken twice daily with food.",
    context=[
        "Take one tablet daily.",
        "May be taken with or without food."
    ]
)

print(result)
# {
#     "status": "BLOCKED",
#     "severity": "HIGH",
#     "reason": "Contradiction detected: frequency mismatch",
#     "confidence": 0.94,
#     "layer": "cascading_nli",
#     "latency_ms": 12
# }
```

### Streaming Verification

```python
# Verify as the LLM generates (reduces time-to-detection)
for chunk in client.verify_stream(
    response_stream=llm.stream(prompt),
    context=retrieved_docs
):
    if chunk["status"] == "BLOCKED":
        print("Early termination: drift detected")
        break
    yield chunk["text"]
```

### Batch Verification

```python
# Verify multiple responses efficiently
results = client.verify_batch([
    {"response": "Answer 1", "context": ["Fact 1"]},
    {"response": "Answer 2", "context": ["Fact 2"]},
])
```

---

## Integration Examples

### LangChain

```python
from tensalis import TensalisClient
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS

guard = TensalisClient(api_key="...")
llm = OpenAI()
vector_db = FAISS.load_local("my_index")

def safe_rag_query(query: str) -> str:
    docs = vector_db.similarity_search(query, k=3)
    context = [doc.page_content for doc in docs]
    response = llm(f"Context: {context}\n\nQuestion: {query}")
    
    result = guard.verify(response=response, context=context)
    
    if result["status"] == "BLOCKED":
        return f"I cannot verify this response. {result['reason']}"
    return response
```

### LlamaIndex

```python
from tensalis import TensalisClient
from llama_index import VectorStoreIndex

guard = TensalisClient(api_key="...")

class TensalisCallback:
    def on_response(self, response, source_nodes):
        context = [node.text for node in source_nodes]
        result = guard.verify(response=str(response), context=context)
        if result["status"] == "BLOCKED":
            raise ValueError(f"Hallucination: {result['reason']}")
```

---

## API Reference

See [docs/api-reference.md](docs/api-reference.md) for complete API documentation.

---

## Configuration

```python
client = TensalisClient(
    api_key="your-api-key",
    endpoint="https://api.tensalis.com/v1",  # or self-hosted
    timeout=30,
    retries=3,
    mode="strict"  # "strict" | "balanced" | "permissive"
)
```

| Mode | Description | Use Case |
|------|-------------|----------|
| `strict` | Block on any uncertainty | Healthcare, Legal, Finance |
| `balanced` | Block on high-confidence issues | General enterprise |
| `permissive` | Block only clear contradictions | Creative applications |

---

## Error Handling

```python
from tensalis import TensalisClient, TensalisAPIError, TensalisError

try:
    result = client.verify(response=text, context=docs)
except TensalisAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
except TensalisError as e:
    print(f"Client error: {e}")
```

---

## Requirements

- Python 3.9+
- `requests >= 2.28.0`

---

## License

This SDK is distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Status

🚧 **Beta Release** - This SDK is functional but under active development. APIs may change before v1.0.

---

## Links

- **Documentation:** https://docs.tensalis.com
- **API Status:** https://status.tensalis.com
- **Support:** support@tensalis.com

---

## Patent Notice

The Tensalis Kinematic Drift Detection engine is protected by pending patent applications. This SDK provides access to the hosted service; the underlying algorithms are proprietary.
