# Agentic Support Platform

An enterprise-style AI customer support platform built with bounded agentic components, grounded retrieval, structured evaluation, and observable execution traces. Uses a synthetic telecom domain.

---

## What This Repo Demonstrates

This platform shows how a production-minded engineering team would design an AI support system — not as a single LLM prompt, but as a structured workflow with distinct responsibilities:

- **Intent classification** — deterministic keyword routing with LLM fallback for ambiguous cases
- **Grounded retrieval** — specialist agents pull evidence from local data before generating responses
- **Diagnostic reasoning** — identifies missing information and asks one focused follow-up question
- **Plan and roaming recommendation** — compares options using retrieved catalog data, explains tradeoffs
- **Escalation logic** — rule-based decisions about when to hand off to human support
- **Evaluation and scoring** — every response is scored on groundedness, completeness, and safety
- **Execution traces** — structured event log for every request, not hidden chain-of-thought
- **Proactive signals** — detects account conditions (high data usage, upcoming travel) before the user complains

---

## Why This Is Not Just a Chatbot

| Generic Chatbot | This Platform |
|---|---|
| Unconstrained multi-turn conversation | Bounded pipeline: intent → retrieval → specialist → evaluation |
| LLM generates answer from nothing | LLM works from retrieved evidence; deterministic fallback always present |
| No observability | Structured trace events on every request |
| No evaluation | Every response scored on 4 dimensions |
| No escalation logic | Rule-based escalation with explicit trigger reasons |
| Reacts to whatever the user says | Proactively detects account conditions |

The orchestrator enforces a fixed flow. Agents cannot call each other arbitrarily. Each specialist handles one class of problem.

---

## Architecture

```
User Message
     │
     ▼
┌─────────────────┐
│  Intent Router  │  Keyword-first classification; LLM fallback for ambiguous cases
└────────┬────────┘
         │ intent + confidence
         ▼
┌─────────────────┐
│ Retrieval Agent │  Searches local data files by intent + message keywords
└────────┬────────┘
         │ evidence[]
         ▼
┌────────────────────────────────────────────────┐
│               Specialist Agent                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────┐ │
│  │  Diagnostic │  │ Recommend.   │  │Billing│ │
│  │   Agent     │  │   Agent      │  │Handler│ │
│  └─────────────┘  └──────────────┘  └───────┘ │
└────────────────────────┬───────────────────────┘
                         │ draft answer
                         ▼
              ┌──────────────────┐
              │ Escalation Agent │  Rule-based; no LLM
              └────────┬─────────┘
                       │ decision
                       ▼
              ┌──────────────────┐
              │ Evaluation Agent │  Scores groundedness, completeness, safety
              └────────┬─────────┘
                       │ scores
                       ▼
                  Final Response
         (answer + intent + evidence_ids +
          escalation + evaluation + trace)
```

The orchestrator in `support_platform/orchestrator.py` owns all routing. No agent calls another agent directly.

---

## Agent Components

### Intent Router (`agents/intent_router.py`)

Classifies requests into one of six intents:

| Intent | Example |
|---|---|
| `billing` | "Why is my bill higher this month?" |
| `plan_recommendation` | "My family uses 80GB/month. Should we change plans?" |
| `roaming` | "I'm traveling to Japan next week." |
| `connectivity_troubleshooting` | "My data stopped working after a plan change." |
| `device_iot_activation` | "My smartwatch won't connect to cellular." |
| `unsupported` | Anything outside supported scope |

Keyword matching runs first. The LLM is only called when confidence is below threshold — keeping most requests fast and deterministic.

### Retrieval Agent (`agents/retrieval_agent.py`)

Searches local files for relevant evidence before any answer is generated:

- `data/plans.json` — plan catalog with prices, data caps, and limitations
- `data/roaming_policies.md` — roaming add-ons by region
- `data/troubleshooting_guides.md` — step-by-step diagnostic guides
- `data/billing_faq.md` — billing explanations and dispute process
- `data/escalation_policy.md` — when and how to escalate

Each retrieved item has an ID (e.g., `roaming_japan_001`) that appears in the response's `evidence_ids` field.

### Diagnostic Agent (`agents/diagnostic_agent.py`)

Handles connectivity and device activation problems.

- Checks for missing information (device type, network type, recent plan change)
- Asks **one** focused follow-up question when a critical slot is missing
- Generates step-by-step resolution steps from retrieved guides when enough context is present
- Escalates automatically if the user has 3+ connectivity tickets in 90 days

### Recommendation Agent (`agents/recommendation_agent.py`)

Handles plan upgrades and roaming add-on selection.

- Compares all plans against user's current usage and account context
- Recommends one primary option with explicit alternatives
- Always includes price, limitations, and a grounded rationale
- Deterministic fallback ensures a recommendation even without LLM access

### Escalation Agent (`agents/escalation_agent.py`)

Fully rule-based. Escalation triggers include:

- Billing action required (refund, dispute, credit)
- Repeated connectivity failures (≥3 tickets in 90 days)
- Live roaming failure while abroad
- Device activation blocked after multiple attempts
- User explicitly requests a human agent
- Unsupported or unsafe request
- Diagnostic confidence below threshold

### Evaluation Agent (`agents/evaluation_agent.py`)

Scores every response before it is returned:

| Dimension | What it measures |
|---|---|
| `groundedness` | Does the answer reference retrieved evidence? |
| `completeness` | Does it address what the user asked? |
| `user_success_likelihood` | Is the user likely to resolve their issue? |
| `safety_correctness` | Was escalation triggered correctly? |
| `fallback_risk` | Overall risk that the response will fail the user |
| `latency_category` | `fast` / `normal` / `slow` |

All scoring is deterministic and rule-based. No LLM call in the evaluation path.

---

## Proactive Support Signals (`proactive/signals.py`)

Given account data, detects:

| Condition | Signal |
|---|---|
| ≥90% of monthly data cap used | Recommend plan upgrade before cycle ends |
| Upcoming travel in ≤14 days with no roaming add-on | Activate roaming before departure |
| ≥3 connectivity tickets in 90 days | Proactive escalation to network team |
| Unlimited plan with very low usage | Consider a lower-cost plan |
| Capped plan consistently near overage | Consider upgrade |

These signals are returned in every response under `proactive_signals` and are independent of the user's question.

---

## Evaluation and Metrics

Run the evaluation harness:

```bash
python scripts/run_eval.py
```

Sample output:

```
──────────────────────────────────────────────────
EVALUATION RESULTS
──────────────────────────────────────────────────
  Total cases:          12
  Passed:               11 / 12
  Success rate:         91.7%
  Escalation accuracy:  100.0%
  Avg groundedness:     0.72
  High fallback rate:   8.3%
──────────────────────────────────────────────────
```

Eval cases cover: plan recommendation, roaming, connectivity with missing slot, billing escalation, unsupported request, repeated failure, proactive trigger, grounded evidence, and trace event generation.

---

## Failure Modes and Escalation

The system is designed to fail safely:

- **Missing slot**: asks one targeted question rather than guessing
- **Low confidence**: escalates to human rather than producing a weak answer
- **No LLM access**: every agent has a deterministic fallback — the system degrades gracefully, never silently
- **Repeated failure pattern**: account history triggers escalation before the user has to ask again
- **Unsafe request**: classified as `unsupported` and immediately escalated

Escalation responses include a synthetic case reference and expected response time.

---

## API Usage

Start the server:

```bash
uvicorn support_platform.api:app --reload
```

**POST /support**

```bash
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I'\''m traveling to Japan next week. What roaming option do I need?",
    "user_id": "demo_user_001",
    "debug": true
  }'
```

Response shape:

```json
{
  "answer": "Based on your usage and needs, here is the recommended roaming option...",
  "intent": "roaming",
  "agent_path": ["intent_router", "retrieval_agent", "recommendation_agent", "evaluation_agent"],
  "evidence_ids": ["roaming_japan_001", "roaming_activation_rules_001"],
  "escalation": false,
  "escalation_reason": null,
  "evaluation": {
    "groundedness": 0.85,
    "completeness": 0.80,
    "user_success_likelihood": 0.75,
    "safety_correctness": 0.90,
    "fallback_risk": "low",
    "latency_category": "fast"
  },
  "trace": [
    {"event_type": "REQUEST_RECEIVED", "reason": "...", "metadata": {}, "timestamp": "..."},
    ...
  ],
  "proactive_signals": [
    "Upcoming trip to Japan in 7 day(s) detected, but no roaming add-on is active."
  ]
}
```

**GET /health**

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "agentic-support-platform"}
```

---

## CLI Usage

```bash
# Basic
python -m support_platform "My mobile data stopped working after I changed plans."

# With user context
python -m support_platform "I'm traveling to Japan next week." --user demo_user_001

# Show trace
python -m support_platform "My smartwatch won't connect." --debug

# Raw JSON output
python -m support_platform "Why is my bill higher?" --json
```

Available demo users: `demo_user_001` through `demo_user_005`, each with different plans, usage levels, and account conditions.

---

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run tests
pytest

# Run eval harness
python scripts/run_eval.py

# Start API
uvicorn support_platform.api:app --reload
```

---

## Repo Structure

```
agentic-support-platform/
  support_platform/
    orchestrator.py        # Central pipeline coordinator
    schemas.py             # Pydantic models for all I/O
    trace.py               # Structured trace event collector
    api.py                 # FastAPI endpoints
    __main__.py            # CLI entry point
    agents/
      intent_router.py     # Keyword + LLM hybrid classifier
      retrieval_agent.py   # Evidence search over local data
      diagnostic_agent.py  # Missing-slot detection + troubleshooting steps
      recommendation_agent.py  # Plan and roaming comparison
      escalation_agent.py  # Rule-based escalation decisions
      evaluation_agent.py  # Response quality scoring
    data/
      loaders.py           # Data file loading and evidence parsing
    proactive/
      signals.py           # Account-level proactive detection
  data/
    plans.json             # Synthetic plan catalog
    roaming_policies.md    # Roaming add-ons by region
    troubleshooting_guides.md  # Diagnostic guides with evidence IDs
    billing_faq.md         # Billing FAQ with evidence IDs
    escalation_policy.md   # Escalation rules with evidence IDs
    device_compatibility.json  # Device and wearable compatibility
    demo_accounts.json     # Synthetic user accounts
  tests/                   # pytest test suite (9 files)
  scripts/
    run_eval.py            # Evaluation harness with aggregate metrics
```

---

## Scope and Non-Goals

**This is a synthetic demo** built to demonstrate enterprise AI support architecture. It is not a production system.

In scope:
- Bounded agentic pipeline with traceable steps
- Grounded retrieval from local data files
- Rule-based escalation and evaluation
- LLM-assisted generation with deterministic fallbacks
- Proactive signal detection from account data
- API + CLI interfaces

Not in scope:
- Real customer data or live network integration
- Multi-turn conversation state (each request is independent)
- Vector embeddings or semantic search (uses keyword matching)
- Authentication, rate limiting, or production security controls
- Fine-tuned models or custom embeddings

The value of this repo is in the **support workflow architecture** — how a team would structure routing, retrieval, diagnostics, escalation, and evaluation in a maintainable, testable system — not in the size of the dataset.
