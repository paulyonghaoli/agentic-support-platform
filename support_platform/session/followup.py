from __future__ import annotations

from support_platform.schemas import Intent

# ---------------------------------------------------------------------------
# Follow-up detection
# ---------------------------------------------------------------------------

_FOLLOWUP_THRESHOLD_WORDS = 10
_CARRYOVER_CONFIDENCE_THRESHOLD = 0.25


def is_followup_response(message: str, session: dict | None, confidence: float) -> bool:
    """
    Returns True when the message looks like an answer to the previous turn's
    follow-up question rather than a new independent request.

    Conditions (all must hold):
    - An active session exists with a last_missing_slot
    - Message is short (≤ N words) OR intent confidence is very low
    """
    if not session:
        return False
    if not session.get("last_missing_slot"):
        return False
    word_count = len(message.strip().split())
    return word_count <= _FOLLOWUP_THRESHOLD_WORDS or confidence < _CARRYOVER_CONFIDENCE_THRESHOLD


def apply_intent_carryover(intent: Intent, confidence: float, session: dict | None) -> Intent:
    """
    If confidence is low and the session has a prior intent, reuse it.
    This handles short follow-up messages like "what about roaming?" or "yes".
    """
    if session and confidence < _CARRYOVER_CONFIDENCE_THRESHOLD:
        stored = session.get("last_intent")
        if stored:
            try:
                return Intent(stored)
            except ValueError:
                pass
    return intent


# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------

def extract_slot_value(slot_name: str, message: str) -> str | None:
    """
    Given the name of the slot we asked about and the user's reply,
    extract the slot value. Returns None if extraction fails.
    """
    msg = message.lower().strip()

    if slot_name == "device_type":
        return _extract_device_type(msg)

    if slot_name == "network_type":
        return _extract_network_type(msg)

    if slot_name in ("recent_plan_change", "wearable_addon"):
        return _extract_yes_no(msg)

    if slot_name == "watch_model":
        return _extract_watch_model(msg)

    if slot_name == "frequency":
        return _extract_frequency(msg)

    if slot_name == "location_type":
        return _extract_location(msg)

    if slot_name == "current_country":
        return _extract_country(msg)

    if slot_name == "roaming_addon":
        return _extract_yes_no(msg)

    if slot_name == "when_started":
        # Free-text; use the message itself if short enough
        if len(message.split()) <= 8:
            return message.strip()
        return None

    if slot_name == "paired_phone":
        return _extract_device_type(msg) or (message.strip() if len(message.split()) <= 5 else None)

    # Generic fallback: if message is very short, use it verbatim
    if len(message.split()) <= 5:
        return message.strip()

    return None


def _extract_device_type(msg: str) -> str | None:
    for keyword, canonical in [
        ("iphone", "iPhone"),
        ("apple", "iPhone"),
        ("ios", "iPhone"),
        ("samsung", "Android (Samsung)"),
        ("galaxy", "Android (Samsung)"),
        ("pixel", "Android (Pixel)"),
        ("android", "Android"),
        ("huawei", "Android (Huawei)"),
        ("oneplus", "Android (OnePlus)"),
    ]:
        if keyword in msg:
            return canonical
    return None


def _extract_network_type(msg: str) -> str | None:
    for keyword, canonical in [
        ("no service", "No Service"),
        ("no signal", "No Signal"),
        ("5g", "5G"),
        ("lte", "LTE"),
        ("4g", "LTE"),
        ("3g", "3G"),
        ("e", "Edge"),
    ]:
        if keyword in msg:
            return canonical
    return None


def _extract_yes_no(msg: str) -> str | None:
    # Check negatives first — "i haven't" must not match "i have"
    no_words = ["haven't", "didn't", "not really", "i don't", "i haven't",
                "i don't have", "no i haven", "nope", "nah", "no i didn"]
    if any(w in msg for w in no_words):
        return "no"
    # Simple "no" only when it's a standalone-ish word
    if msg.strip() in ("no", "nope", "nah") or msg.startswith("no ") or msg.startswith("no,"):
        return "no"
    yes_words = ["yes", "yeah", "yep", "yup", "correct", "right", "i did", "i changed",
                 "recently", "just did", "i have", "activated", "i do"]
    if any(w in msg for w in yes_words):
        return "yes"
    return None


def _extract_watch_model(msg: str) -> str | None:
    for keyword, canonical in [
        ("apple watch ultra", "Apple Watch Ultra"),
        ("apple watch series 9", "Apple Watch Series 9"),
        ("apple watch series 8", "Apple Watch Series 8"),
        ("apple watch series 7", "Apple Watch Series 7"),
        ("apple watch", "Apple Watch"),
        ("galaxy watch 6", "Samsung Galaxy Watch 6"),
        ("galaxy watch 5", "Samsung Galaxy Watch 5"),
        ("galaxy watch 4", "Samsung Galaxy Watch 4"),
        ("galaxy watch", "Samsung Galaxy Watch"),
        ("samsung watch", "Samsung Galaxy Watch"),
        ("fitbit", "Fitbit"),
        ("garmin", "Garmin"),
    ]:
        if keyword in msg:
            return canonical
    return None


def _extract_frequency(msg: str) -> str | None:
    if any(w in msg for w in ["always", "constant", "all the time", "never connects", "never works"]):
        return "constant"
    if any(w in msg for w in ["sometimes", "intermittent", "comes and goes", "occasionally", "random"]):
        return "intermittent"
    return None


def _extract_location(msg: str) -> str | None:
    if any(w in msg for w in ["home", "house", "apartment", "flat"]):
        return "home"
    if any(w in msg for w in ["office", "work", "workplace"]):
        return "office"
    if "building" in msg:
        return "building"
    if "basement" in msg:
        return "basement"
    return None


def _extract_country(msg: str) -> str | None:
    # Common countries mentioned in support scenarios
    countries = [
        "japan", "south korea", "korea", "france", "germany", "uk", "united kingdom",
        "spain", "italy", "australia", "canada", "mexico", "brazil", "singapore",
        "hong kong", "thailand", "india", "uae", "dubai",
    ]
    for country in countries:
        if country in msg:
            return country.title()
    # If short message, use verbatim
    if len(msg.split()) <= 3:
        return msg.strip().title()
    return None
