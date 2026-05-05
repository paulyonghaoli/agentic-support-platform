from __future__ import annotations

import pytest

from support_platform.agents.intent_router import IntentRouter
from support_platform.schemas import Intent


@pytest.fixture
def router() -> IntentRouter:
    return IntentRouter(client=None, use_llm_fallback=False)


@pytest.mark.parametrize("message,expected_intent", [
    ("My mobile data stopped working after I changed plans.", Intent.CONNECTIVITY_TROUBLESHOOTING),
    ("I keep losing signal indoors.", Intent.CONNECTIVITY_TROUBLESHOOTING),
    ("I'm traveling to Japan next week. What roaming option do I need?", Intent.ROAMING),
    ("I'm going to Europe next month.", Intent.ROAMING),
    ("My family uses around 80GB per month. Should we change plans?", Intent.PLAN_RECOMMENDATION),
    ("Which plan should I upgrade to?", Intent.PLAN_RECOMMENDATION),
    ("My smartwatch is not connecting.", Intent.DEVICE_IOT_ACTIVATION),
    ("How do I activate my Apple Watch?", Intent.DEVICE_IOT_ACTIVATION),
    ("Why is my bill higher this month?", Intent.BILLING),
    ("I was overcharged this month.", Intent.BILLING),
])
def test_intent_routing_keyword(router, message, expected_intent):
    intent, confidence = router.route(message)
    assert intent == expected_intent, f"Message: '{message}' → got {intent}, expected {expected_intent}"
    assert confidence > 0.0


def test_unsupported_intent_returns_unsupported(router):
    intent, confidence = router.route("What is the weather like in Tokyo?")
    assert intent == Intent.UNSUPPORTED
    assert confidence == 0.0


def test_intent_confidence_is_between_0_and_1(router):
    _, confidence = router.route("My bill is too high this month.")
    assert 0.0 <= confidence <= 1.0


def test_billing_dispute_keywords(router):
    intent, _ = router.route("I want to dispute a charge on my invoice.")
    assert intent == Intent.BILLING


def test_roaming_travel_keywords(router):
    intent, _ = router.route("I'm flying to South Korea for two weeks.")
    assert intent == Intent.ROAMING


def test_connectivity_no_signal(router):
    intent, _ = router.route("I have no signal in my office building.")
    assert intent == Intent.CONNECTIVITY_TROUBLESHOOTING
