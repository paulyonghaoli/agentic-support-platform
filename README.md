# Agentic Support Platform

An enterprise-style AI customer support platform built with bounded agentic components, grounded retrieval, structured evaluation, observable execution traces, multi-turn conversational state, and a voice interface. Uses a synthetic telecom domain.

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
- **Multi-turn conversational state** — session-based slot filling and intent carry-over across turns
- **Voice interface** — speech-to-text + text-to-speech wrapping the same pipeline, not separate logic

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
    session/
      store.py             # In-memory session store with TTL
      followup.py          # Follow-up detection, slot extraction, intent carry-over
    voice/
      speech_to_text.py    # Whisper STT or mock fallback
      text_to_speech.py    # OpenAI TTS or stub fallback
      voice_session.py     # Voice pipeline coordinator + CLI entry point
    web/
      voice_demo.html      # Browser live-voice demo (Web Speech API -> POST /support)
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

## Multi-turn Conversations

Each user has a session that persists across requests within the same server process (30-minute TTL, in-memory). The orchestrator loads and saves session state on every turn.

### How it works

**Slot filling:** When the diagnostic agent asks a follow-up question (e.g., "What device are you using?"), the missing slot name is stored in the session. On the next turn, if the message is short or low-confidence, the system detects it as a follow-up answer, extracts the slot value, and resumes the diagnostic without re-asking.

**Intent carry-over:** If a short message has very low intent confidence (e.g., "yes", "iPhone", "it comes and goes"), the system reuses the previous turn's intent rather than classifying the message in isolation.

**Session state in every response:** Each response includes a `session_state_summary`:

```json
{
  "intent": "connectivity_troubleshooting",
  "known_slots": {"device_type": "iPhone"},
  "missing_slots": ["network_type"],
  "turn_count": 2
}
```

### Example

```
Turn 1
  User:   My data stopped working.
  System: To help diagnose your issue, I need a bit more information:
          What device are you using, and what does your signal bar show?

Turn 2
  User:   It's an iPhone.
  System: Here are the recommended steps to resolve your issue:
          1. Toggle airplane mode off and on on iPhone to force network re-registration.
          2. Restart your device.
          3. Check APN settings are set to 'synthtel.net'.
```

The second turn detects the short message as a follow-up, fills `device_type = "iPhone"`, carries over the `connectivity_troubleshooting` intent, and produces diagnostic steps — no repeated question.

### Design constraints

- No vector DB or embeddings — slots are extracted with deterministic pattern matching
- Sessions are per-user, not per-conversation thread
- Max 10 messages kept in history; sessions expire after 30 minutes
- The orchestrator never loops — each turn is one bounded pipeline pass

---

## Voice Interface

Voice is a thin wrapper around the existing support pipeline. No logic is duplicated.

```
audio file
    │
    ▼
speech_to_text.transcribe()          ← OpenAI Whisper or mock fallback
    │ transcript (plain text)
    ▼
orchestrator.handle(SupportRequest)  ← same pipeline as /support
    │ SupportResponse
    ▼
text_to_speech.synthesize()          ← OpenAI TTS or stub fallback
    │ audio file path
    ▼
VoiceResponse (transcript + answer + audio_path + trace)
```

Both STT and TTS degrade gracefully: if no API key is available, STT returns a mock transcript based on filename, and TTS writes a plain text stub. The support pipeline itself always runs.

### Voice API

```bash
# Upload audio, get transcript + answer + synthesized audio path
curl -X POST http://localhost:8000/voice-support \
  -F "audio=@query.wav" \
  -F "user_id=demo_user_001"
```

### Voice CLI

```bash
python -m support_platform.voice path/to/audio.wav --user demo_user_001
python -m support_platform.voice path/to/audio.wav --debug   # show trace
python -m support_platform.voice path/to/audio.wav --json    # raw JSON
```

### Modules

| File | Role |
| --- | --- |
| `voice/speech_to_text.py` | `transcribe(audio_path)` — Whisper API or mock |
| `voice/text_to_speech.py` | `synthesize(text)` — TTS API or stub |
| `voice/voice_session.py` | Pipeline coordinator + CLI entry point |

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
- Vector embeddings or semantic search (uses keyword matching)
- Authentication, rate limiting, or production security controls
- Fine-tuned models or custom embeddings

The value of this repo is in the **support workflow architecture** — how a team would structure routing, retrieval, diagnostics, escalation, and evaluation in a maintainable, testable system — not in the size of the dataset.

---

## Live Voice Demo

Open `GET /voice-demo` in Chrome or Edge while the server is running. The page uses the browser's built-in **Web Speech API** for speech recognition and **SpeechSynthesis** for playback — no audio is sent to the server.

### Start the server

```bash
uvicorn support_platform.api:app --reload
# Then open: http://localhost:8000/voice-demo
```

### Demo script

| Say | What it exercises |
| --- | --- |
| "My data stopped working." | Diagnostic agent asks a follow-up question (missing slot) |
| "It's an iPhone." | Slot filling — resumes diagnostic without re-asking |
| "I'm traveling to Japan next week." | Roaming recommendation + proactive signals for demo_user_001 |
| "Why is my bill higher this month?" | Billing FAQ retrieval |
| "I want a refund." | Rule-based escalation + escalation badge |
| "Can you access my neighbor's account?" | Unsupported intent — immediate escalation |

Switch between the five demo accounts in the dropdown to see different proactive signals and account conditions.

### Browser note

Web Speech API is only supported in Chrome and Edge. Firefox and Safari users will see the microphone button disabled. The `/support` API itself works in all browsers and with any HTTP client.

---

## Real-World Failure Walkthroughs

These scenarios show how the system handles degraded conditions without silently failing.

### 1. No OpenAI API key

**What happens:** Every agent has a deterministic fallback path. The intent router uses keyword matching only (no LLM fallback). The diagnostic and recommendation agents use template responses from retrieved evidence. The evaluation agent is fully deterministic and needs no LLM. The voice STT returns a mock transcript based on the audio filename; TTS writes a plain-text stub.

**Effect:** Users get slightly less nuanced answers — but they always get _an_ answer. No 500 errors, no silent empty responses.

### 2. Unknown intent with high ambiguity

**Request:** "Something weird happened with my account."

**What happens:** Keyword matching scores zero on all intents. With an API key, the LLM classifies with low confidence (< 0.3). The escalation agent's `low_confidence` rule triggers. The user receives a polite escalation response with a case reference and expected response time.

**Effect:** Ambiguous requests never produce hallucinated answers — they route to human support.

### 3. Repeated connectivity failures

**Account:** `demo_user_004` (Priya — 4 connectivity tickets in 90 days).

**Request:** "I keep losing signal indoors."

**What happens:** The diagnostic agent runs normally and would produce troubleshooting steps — but the escalation agent reads `connectivity_tickets_last_90d >= 3` from the account and overrides the diagnostic answer with a network-team escalation. The proactive signals module also flags this account independently.

**Effect:** The system detects repeat-failure patterns from account history before the user has to ask again.

---

## Design Tradeoffs

| Decision | Alternative | Why this was chosen |
| --- | --- | --- |
| Keyword-first routing with LLM fallback | LLM-only classification | Keeps most requests fast and deterministic; LLM is only called when keywords are ambiguous. Reduces cost and latency for the majority of production traffic. |
| Deterministic evaluation (no LLM) | LLM-as-judge scoring | Evaluation must be stable and cheap. LLM judges introduce variance, cost per-response, and a circular dependency (the model judges itself). |
| Rule-based escalation | LLM-based triage | Escalation decisions are binary and consequential. Rules are auditable, testable, and predictable — LLM outputs in escalation paths create liability. |
| In-memory session store | Redis / database | For a single-server demo, in-memory is zero-dependency and fast. A production system would replace `SessionStore` with Redis using the same interface. |
| Keyword slot extraction | NER / embeddings | Avoids runtime model dependency for slot filling. Coverage is sufficient for the bounded slot set (device_type, network_type, yes/no) and is trivially testable. |

---

## Known Limitations

1. **Session is per-process.** The in-memory store is lost on server restart. Multiple API workers (e.g., `--workers 4`) would give each worker separate sessions — sticky routing or an external store would be required.

2. **Intent routing is substring-based.** "change plans" matches `plan_recommendation` even when embedded in "I don't want to change plans." Phrase matching could improve precision.

3. **Slot extraction is English-only.** `_extract_yes_no`, `_extract_device_type`, etc. rely on English keywords. Internationalisation would need per-locale extraction logic or an NLU layer.

4. **Evidence retrieval is keyword hit-count.** Two pieces of evidence with different specificity score equally if they share the same keywords. BM25 or embedding similarity would improve ranking.

5. **TTS output is not streamed.** The voice pipeline synthesizes a complete audio file before responding. For long answers, this adds latency. Streaming TTS (chunked response) would improve perceived responsiveness.

6. **Evaluation scores are heuristics.** Groundedness is measured by evidence ID substring matching in the answer — a model that quotes IDs verbatim would score perfectly even if the answer were wrong. Human evaluation or a separate grounding model would be more robust.

---

## Production Extensions

The architecture is designed so each component can be replaced independently.

| Component | Production replacement |
| --- | --- |
| In-memory session store | Redis with the same `SessionStore` interface |
| Keyword slot extraction | spaCy NER or a fine-tuned slot-filling model |
| Local file retrieval | Vector store (Pinecone, Weaviate) with BM25 hybrid search |
| In-process orchestrator | Durable workflow engine (Temporal, Inngest) for retry, timeout, and audit |
| Synthetic demo accounts | CRM / account API integration |
| Rule-based evaluation | LLM-as-judge with calibrated rubrics, or human eval via annotation pipeline |
| Single-worker FastAPI | Gunicorn + uvicorn workers behind a load balancer with Redis session store |
