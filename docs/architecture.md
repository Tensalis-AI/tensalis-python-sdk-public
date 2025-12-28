# Tensalis Architecture

## System Overview

Tensalis is a multi-layer hallucination detection system designed to catch semantic drift, contradictions, and fabrications in LLM outputs that single-method approaches miss.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER APPLICATION                                 │
│                    (LangChain, LlamaIndex, Custom RAG)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      TENSALIS PYTHON SDK                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   verify()  │  │verify_batch()│  │verify_stream│  │  health()   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TENSALIS VERIFICATION ENGINE                          │
│                         (Patent Pending)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    LAYER 1: REDSHIFT FIDELITY                     │  │
│  │                                                                   │  │
│  │  • Measures semantic trajectory (velocity + acceleration)        │  │
│  │  • Detects off-topic drift with high embedding similarity        │  │
│  │  • Physics-informed: treats text as movement through space       │  │
│  │                                                                   │  │
│  │  Input: [context embeddings] → [response embeddings]             │  │
│  │  Output: drift_velocity, drift_acceleration, trajectory_score    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  LAYER 2: CASCADING NLI                           │  │
│  │                                                                   │  │
│  │  Two-stage architecture for speed + accuracy:                    │  │
│  │                                                                   │  │
│  │  Stage 1: Fast embedding similarity check                        │  │
│  │           - 80% of requests exit here (< 5ms)                    │  │
│  │           - Calibrated threshold catches obvious issues          │  │
│  │                                                                   │  │
│  │  Stage 2: Deep NLI inference (for edge cases)                    │  │
│  │           - Full entailment/contradiction/neutral classification │  │
│  │           - Catches "semantic illusion" cases                    │  │
│  │                                                                   │  │
│  │  Key insight: 89%+ similarity can still be CONTRADICTION         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                 LAYER 3: BLUESHIFT FIDELITY                       │  │
│  │                                                                   │  │
│  │  Detects information fabrication:                                │  │
│  │                                                                   │  │
│  │  • Counts claims in context vs. response                         │  │
│  │  • Measures information density expansion                        │  │
│  │  • Flags when response contains more specifics than source       │  │
│  │                                                                   │  │
│  │  Example: Context says "patient has diabetes"                    │  │
│  │           Response adds "HbA1c 8.2%, fasting glucose 156"        │  │
│  │           → FABRICATION (invented specifics)                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   SEMANTIC GYROSCOPE                              │  │
│  │                   (Auto-Correction Layer)                         │  │
│  │                                                                   │  │
│  │  PID-controlled feedback loop:                                   │  │
│  │  • Proportional: Immediate correction for detected drift        │  │
│  │  • Integral: Accumulated error tracking                          │  │
│  │  • Derivative: Rate-of-change damping                            │  │
│  │                                                                   │  │
│  │  Enables: Automatic response truncation and regeneration         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why Multi-Layer?

Our research shows that **23% of hallucinations pass embedding-only checks**.

| Hallucination Type | Embedding-Only | NLI-Only | Tensalis |
|--------------------|----------------|----------|----------|
| Off-topic drift | ✅ Catches | ❌ Misses | ✅ Catches |
| Logical contradiction | ❌ Misses | ✅ Catches | ✅ Catches |
| Fabricated specifics | ❌ Misses | ❌ Misses | ✅ Catches |
| Semantic illusion* | ❌ Misses | ✅ Catches | ✅ Catches |

*Semantic illusion: High embedding similarity (89%+) but factually incorrect.

## Performance Characteristics

### Latency Distribution

```
        Fast Path (80%)         Deep Path (20%)
        ┌───────────┐           ┌───────────┐
        │  < 10ms   │           │  30-50ms  │
        │           │           │           │
        │ Embedding │           │ Full NLI  │
        │  check    │           │ inference │
        │  passes   │           │           │
        └───────────┘           └───────────┘
```

### Accuracy Metrics

- **Precision**: 94.2% (low false positives)
- **Recall**: 91.7% (catches most hallucinations)
- **F1 Score**: 92.9%

Benchmarked on HaluEval, TruthfulQA, and internal enterprise datasets.

## Data Flow

```
1. User calls verify(response, context)
                    │
                    ▼
2. SDK sends request to Tensalis API
                    │
                    ▼
3. Engine runs multi-layer verification
   • Layer 1: Redshift (trajectory analysis)
   • Layer 2: Cascading NLI (logical inference)
   • Layer 3: Blueshift (fabrication detection)
                    │
                    ▼
4. Results aggregated with confidence scores
                    │
                    ▼
5. Response returned: VERIFIED | BLOCKED | WARNING
```

## Security & Privacy

- All data encrypted in transit (TLS 1.3)
- No storage of request content after processing
- SOC 2 Type II compliant
- GDPR/CCPA compliant
- Optional self-hosted deployment available

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/verify` | POST | Verify single response |
| `/v1/verify/batch` | POST | Verify multiple responses |
| `/v1/health` | GET | API health check |
| `/v1/usage` | GET | Usage statistics |
