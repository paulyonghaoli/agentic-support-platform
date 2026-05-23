"""
Eval cases for RAG quality measurement.

Each case has a question and an optional ground_truth answer.
Ground truth is used to compute context recall (did the retrieved
chunks contain the information needed to answer correctly?).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EvalCase:
    question: str
    user_id: str = "user_001"
    ground_truth: Optional[str] = None


EVAL_CASES: list[EvalCase] = [
    # --- Billing ---
    EvalCase(
        question="Why is my bill higher than usual this month?",
        user_id="user_001",
        ground_truth=(
            "Your bill may be higher due to roaming charges, data overage fees, "
            "or a third-party subscription added to your account. "
            "Review your itemised bill to identify the specific charge."
        ),
    ),
    EvalCase(
        question="I want a refund for an unauthorized charge on my account.",
        user_id="user_001",
        ground_truth=(
            "You can dispute an unauthorized charge by contacting support. "
            "Refunds for billing errors are typically processed within 1-2 billing cycles."
        ),
    ),
    EvalCase(
        question="My statement has an unexpected item I don't recognise.",
        user_id="user_001",
        ground_truth=(
            "Unrecognised charges may be third-party subscriptions or roaming fees. "
            "Contact support to investigate and remove the charge if it is an error."
        ),
    ),

    # --- Connectivity ---
    EvalCase(
        question="My phone keeps cutting out inside the house.",
        user_id="user_002",
        ground_truth=(
            "Poor indoor signal can be caused by building materials blocking the signal. "
            "Try Wi-Fi Calling if your phone supports it, or a signal booster for persistent issues."
        ),
    ),
    EvalCase(
        question="Cellular radio won't lock on to any band.",
        user_id="user_002",
        ground_truth=(
            "Try toggling airplane mode on and off, or manually selecting a network in settings. "
            "A SIM re-seat or factory reset of network settings may also resolve the issue."
        ),
    ),
    EvalCase(
        question="My data is really slow even though I have signal.",
        user_id="user_002",
        ground_truth=(
            "Slow data with good signal may indicate you have reached your high-speed data cap "
            "and are now on throttled speeds. Check your data usage in the app."
        ),
    ),

    # --- Roaming ---
    EvalCase(
        question="I'm heading to Tokyo next week, will my phone work?",
        user_id="user_003",
        ground_truth=(
            "Japan is covered by international roaming. "
            "Add a roaming pass before you travel to avoid per-MB charges. "
            "Check the Japan & Korea roaming pack for the best rates."
        ),
    ),
    EvalCase(
        question="I landed in Paris and none of my apps are loading.",
        user_id="user_003",
        ground_truth=(
            "Ensure international roaming is enabled on your account and your phone. "
            "France is covered under the Europe roaming pack. "
            "If roaming is active but data is not working, try toggling airplane mode."
        ),
    ),

    # --- Plans ---
    EvalCase(
        question="What's the cheapest plan that includes hotspot?",
        user_id="user_004",
        ground_truth=None,  # No fixed ground truth — depends on current plan catalogue
    ),
    EvalCase(
        question="I want unlimited data for my whole family.",
        user_id="user_004",
        ground_truth=None,
    ),

    # --- Device / IoT ---
    EvalCase(
        question="My smartwatch lost its independent data connection.",
        user_id="user_005",
        ground_truth=(
            "The watch needs a Cellular/LTE plan linked to your account. "
            "Ensure the watch SIM or eSIM is activated and the watch is paired to your phone."
        ),
    ),
    EvalCase(
        question="How do I activate a new SIM card?",
        user_id="user_005",
        ground_truth=(
            "Insert the SIM, restart your device, and follow the activation steps in the app "
            "or on the website. Allow up to 24 hours for full activation."
        ),
    ),
]
