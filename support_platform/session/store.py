from __future__ import annotations

import time
from typing import Any

_DEFAULT_TTL = 1800  # 30 minutes
_MAX_HISTORY = 10   # messages kept per session


class SessionStore:
    """
    In-memory session store keyed by user_id.

    Each session holds:
        messages       — recent turn history (list of {"role", "content"})
        last_intent    — most recent classified intent string
        slots          — filled slot values {"device_type": "iPhone", ...}
        last_missing_slot — slot name we asked about last turn
        last_response  — the answer we sent last turn
        turn_count     — total turns in this session
        timestamp      — unix time of last update (used for TTL)
    """

    def __init__(self, ttl_seconds: int = _DEFAULT_TTL) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def get(self, user_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(user_id)
        if session is None:
            return None
        if time.time() - session["timestamp"] > self._ttl:
            del self._sessions[user_id]
            return None
        return session

    def update(self, user_id: str, **kwargs: Any) -> None:
        existing = self.get(user_id)
        if existing is None:
            existing = {
                "messages": [],
                "last_intent": None,
                "slots": {},
                "last_missing_slot": None,
                "last_response": None,
                "turn_count": 0,
                "timestamp": time.time(),
            }

        for key, value in kwargs.items():
            if key == "slots" and isinstance(value, dict):
                # Merge slots rather than replace
                existing["slots"].update(value)
            elif key == "add_message" and isinstance(value, dict):
                existing["messages"].append(value)
                # Trim to max history (keep pairs: last N/2 user+assistant turns)
                if len(existing["messages"]) > _MAX_HISTORY:
                    existing["messages"] = existing["messages"][-_MAX_HISTORY:]
            else:
                existing[key] = value

        existing["timestamp"] = time.time()
        self._sessions[user_id] = existing

    def increment_turn(self, user_id: str) -> None:
        session = self.get(user_id)
        count = (session or {}).get("turn_count", 0)
        self.update(user_id, turn_count=count + 1)

    def clear(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)

    def active_count(self) -> int:
        now = time.time()
        return sum(
            1 for s in self._sessions.values()
            if now - s["timestamp"] <= self._ttl
        )


# Module-level singleton
_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
