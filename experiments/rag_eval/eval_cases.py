"""
Eval cases for RAG quality measurement.

Covers a realistic spread of user personas and conversation styles:
  - Casual / informal phrasing
  - Angry / frustrated users demanding resolution
  - Chatty / verbose users burying the question in context
  - Technical users with precise jargon
  - ESL users with non-native phrasing
  - Senior / low-tech users
  - Multi-turn back-and-forth conversations

Multi-turn conversations are run sequentially under one user_id so session
state (intent carry-over, slot memory) is exercised. Every turn becomes its
own EvalRecord so we get per-turn faithfulness and relevance scores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Single-turn cases
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    question: str
    user_id: str = "user_001"
    ground_truth: Optional[str] = None
    persona: str = "neutral"


# ---------------------------------------------------------------------------
# Multi-turn conversation cases
# ---------------------------------------------------------------------------

@dataclass
class Turn:
    message: str
    ground_truth: Optional[str] = None


@dataclass
class ConversationCase:
    turns: list[Turn]
    user_id: str = "user_001"
    description: str = ""
    persona: str = "neutral"


# ===========================================================================
# BILLING
# ===========================================================================

BILLING_CASES: list[EvalCase] = [
    # Casual
    EvalCase(
        question="hey so my bill seems a bit higher than last month, any idea why?",
        user_id="user_001",
        persona="casual",
        ground_truth=(
            "Your bill may be higher due to roaming charges, data overage fees, "
            "or a third-party subscription. Check your itemised bill to identify "
            "the specific charge."
        ),
    ),
    # Angry
    EvalCase(
        question=(
            "I AM ABSOLUTELY FURIOUS. You charged me $47 for international roaming "
            "that I NEVER activated. I want a full refund NOW and I want to know "
            "how this even happened."
        ),
        user_id="user_001",
        persona="angry",
        ground_truth=(
            "Unexpected roaming charges can be disputed. Contact support to review "
            "the charge. If it was applied in error, a refund will be processed "
            "within 1–2 billing cycles."
        ),
    ),
    # Chatty / verbose
    EvalCase(
        question=(
            "So I got my bill this morning and I was honestly pretty surprised "
            "because last month I paid around $65 and now it's showing $89 and I "
            "genuinely have no idea what changed — I didn't travel, I didn't "
            "download any more stuff than usual, I haven't changed my plan or "
            "anything like that. Is there some kind of system error maybe? Or did "
            "something get added without me knowing?"
        ),
        user_id="user_001",
        persona="chatty",
        ground_truth=(
            "A sudden bill increase without obvious cause is often due to a "
            "third-party subscription, a prorated plan change, or a one-time fee. "
            "Review your itemised bill or contact support to identify the charge."
        ),
    ),
    # Technical
    EvalCase(
        question=(
            "There's an unauthorized third-party charge from 'PREMIA SMS' on my "
            "account. I need this reversed immediately and the subscription blocked "
            "at the carrier level."
        ),
        user_id="user_001",
        persona="technical",
        ground_truth=(
            "Third-party charges from premium SMS services can be disputed and "
            "blocked. Contact support to remove the charge and enable third-party "
            "billing blocks on your account."
        ),
    ),
    # ESL
    EvalCase(
        question="my bill have charge I not understand, maybe mistake? can you help explain?",
        user_id="user_001",
        persona="esl",
        ground_truth=(
            "An unrecognised charge may be a roaming fee, overage, or third-party "
            "subscription. Contact support with the charge details to investigate."
        ),
    ),
    # Senior
    EvalCase(
        question=(
            "My daughter set up this phone for me. I got a letter saying my bill "
            "went up but I didn't do anything different. Is someone using my phone "
            "without my knowing?"
        ),
        user_id="user_001",
        persona="senior",
        ground_truth=(
            "Unexpected bill increases are usually due to data overages or new "
            "charges, not unauthorised use. Contact support to review your recent "
            "charges and ensure your account is secure."
        ),
    ),
]

# ---------------------------------------------------------------------------
# Billing multi-turn conversations
# ---------------------------------------------------------------------------

BILLING_CONVERSATIONS: list[ConversationCase] = [
    ConversationCase(
        description="Customer confused about billing cycle, escalates to refund request",
        user_id="user_conv_01",
        persona="casual-to-frustrated",
        turns=[
            Turn(
                message="why is my bill higher this month",
                ground_truth=None,
            ),
            Turn(
                message="what even is a billing cycle? i don't really get it",
                ground_truth=(
                    "A billing cycle is the monthly period your usage is measured "
                    "over. Charges from the previous cycle appear on the next bill."
                ),
            ),
            Turn(
                message=(
                    "okay so if there's a roaming charge from last month that was "
                    "wrong, when would I see the refund?"
                ),
                ground_truth=(
                    "Refunds for billing errors are typically applied within 1–2 "
                    "billing cycles and will appear as a credit on your next bill."
                ),
            ),
        ],
    ),
    ConversationCase(
        description="Angry customer demanding immediate refund, then calming down",
        user_id="user_conv_02",
        persona="angry",
        turns=[
            Turn(
                message=(
                    "This is OUTRAGEOUS. I have a $200 bill and I want a refund "
                    "RIGHT NOW."
                ),
                ground_truth=None,
            ),
            Turn(
                message="fine, what information do you need from me to process this?",
                ground_truth=None,
            ),
            Turn(
                message="and how long will the investigation take?",
                ground_truth=(
                    "Billing dispute investigations typically take 3–5 business days. "
                    "You will be notified of the outcome by email or SMS."
                ),
            ),
        ],
    ),
]


# ===========================================================================
# CONNECTIVITY
# ===========================================================================

CONNECTIVITY_CASES: list[EvalCase] = [
    # Casual
    EvalCase(
        question="ugh my signal keeps dropping inside my apartment, it's really annoying",
        user_id="user_002",
        persona="casual",
        ground_truth=(
            "Poor indoor signal can be caused by building materials. Try enabling "
            "Wi-Fi Calling in your phone settings as an immediate workaround."
        ),
    ),
    # Angry
    EvalCase(
        question=(
            "This is the FIFTH TIME this week my data has cut out completely. "
            "I'm paying $80 a month for a service that barely works. "
            "What are you going to do about this?"
        ),
        user_id="user_002",
        persona="angry",
        ground_truth=(
            "Repeated connectivity failures may indicate a network issue in your "
            "area or a problem with your SIM or device. A case can be escalated "
            "for a network investigation."
        ),
    ),
    # Chatty
    EvalCase(
        question=(
            "So I live in this old brick building from the 1920s — beautiful place "
            "but the walls are super thick — and for the first year I was here the "
            "signal was fine, like 3–4 bars, but in the last few weeks it's been "
            "dropping to zero constantly, especially in my bedroom at the back. "
            "I haven't changed anything on my phone. Could there be a tower issue "
            "or something?"
        ),
        user_id="user_002",
        persona="chatty",
        ground_truth=(
            "Thick building materials reduce indoor signal. A recent tower outage "
            "or configuration change could also explain a sudden drop. "
            "Try Wi-Fi Calling and check the network status page for outages in "
            "your area."
        ),
    ),
    # Technical
    EvalCase(
        question=(
            "I'm on Band 12 (700 MHz) which should penetrate buildings well, "
            "but I'm only getting 1–2 bars indoors and frequently dropping to "
            "HSPA+. APN settings look correct. Could this be a SIM provisioning "
            "issue or is the tower underloaded?"
        ),
        user_id="user_002",
        persona="technical",
        ground_truth=(
            "Persistent LTE fallback with correct APN settings may indicate "
            "a SIM provisioning issue or localised tower congestion. "
            "A network team investigation would be needed to diagnose further."
        ),
    ),
    # ESL
    EvalCase(
        question="internet not work since yesterday morning. I restart phone but same problem. what I do?",
        user_id="user_002",
        persona="esl",
        ground_truth=(
            "Try toggling airplane mode on and off after restarting. "
            "If data is still not working, check if you have reached your "
            "monthly data limit or contact support for further diagnostics."
        ),
    ),
    # Senior
    EvalCase(
        question=(
            "My phone keeps saying 'No Service' and I don't know what that means. "
            "It was working perfectly last week. I haven't dropped it or anything. "
            "Did I do something wrong?"
        ),
        user_id="user_002",
        persona="senior",
        ground_truth=(
            "A 'No Service' message means the phone cannot connect to the network. "
            "Try turning the phone off and back on. If it persists, the SIM card "
            "may need to be reseated or replaced."
        ),
    ),
]

CONNECTIVITY_CONVERSATIONS: list[ConversationCase] = [
    ConversationCase(
        description="Step-by-step troubleshooting — customer has already tried the basics",
        user_id="user_conv_03",
        persona="cooperative",
        turns=[
            Turn(message="my data isn't working at all"),
            Turn(message="yeah I already restarted it, didn't help"),
            Turn(
                message="okay I tried airplane mode too, still nothing. what else can I try?",
                ground_truth=(
                    "If restarting and airplane mode have not helped, try removing "
                    "and reinserting the SIM card. If the issue persists, a SIM "
                    "replacement or network investigation may be needed."
                ),
            ),
        ],
    ),
    ConversationCase(
        description="Frustrated customer escalating repeated outages",
        user_id="user_conv_04",
        persona="angry",
        turns=[
            Turn(message="my connection dropped again. this keeps happening every day"),
            Turn(message="I want this investigated properly, not just told to restart my phone"),
            Turn(
                message="fine, what details do you need to open a network ticket?",
                ground_truth=None,
            ),
        ],
    ),
]


# ===========================================================================
# ROAMING
# ===========================================================================

ROAMING_CASES: list[EvalCase] = [
    # Casual
    EvalCase(
        question="heading to europe next month, do I need to do anything for my phone to work?",
        user_id="user_003",
        persona="casual",
        ground_truth=(
            "Add a Europe roaming pass before you travel to avoid per-MB charges. "
            "Ensure roaming is enabled on your account and device."
        ),
    ),
    # Angry — abroad right now
    EvalCase(
        question=(
            "I just landed in Tokyo an hour ago and my phone has NO data whatsoever. "
            "I specifically asked about international coverage before my trip and "
            "was told it would work. This is completely unacceptable."
        ),
        user_id="user_003",
        persona="angry",
        ground_truth=(
            "Ensure international roaming is enabled on your account and that "
            "your phone's roaming setting is turned on. Toggle airplane mode to "
            "force a network reconnection. If the issue persists, contact support "
            "for an emergency roaming fix."
        ),
    ),
    # Chatty — multi-country trip
    EvalCase(
        question=(
            "So my partner and I are planning this amazing trip — we're doing "
            "London for 3 nights, then Paris for 4 nights, then a quick overnight "
            "in Amsterdam. We both have phones on this network. I want to make "
            "sure we can use Google Maps and WhatsApp everywhere without coming "
            "home to a massive bill. What's the best way to set this up?"
        ),
        user_id="user_003",
        persona="chatty",
        ground_truth=(
            "A Europe roaming pass covers the UK, France, and Netherlands. "
            "Add it before departure and enable roaming on both devices. "
            "WhatsApp and Google Maps will work normally within the data allowance."
        ),
    ),
    # Technical
    EvalCase(
        question=(
            "I'm in Seoul on a partner network (KT Corp). My device shows 4G LTE "
            "but data sessions are timing out. I've confirmed the roaming APN is "
            "set to 'epc.tmobile.com'. Is there a known inter-carrier routing "
            "issue or should I try manual network selection?"
        ),
        user_id="user_003",
        persona="technical",
        ground_truth=(
            "APN timeout issues on partner networks in Korea may require a "
            "manual network selection reset or APN update. "
            "Contact support to confirm the correct roaming APN for KT Corp "
            "and to verify your roaming provisioning."
        ),
    ),
]

ROAMING_CONVERSATIONS: list[ConversationCase] = [
    ConversationCase(
        description="Customer planning trip, asking follow-up questions about Japan roaming",
        user_id="user_conv_05",
        persona="casual",
        turns=[
            Turn(message="I'm going to Japan next week, will my phone work?"),
            Turn(
                message="how much does the Japan roaming add-on cost?",
                ground_truth=None,
            ),
            Turn(
                message="is there a data limit on that or is it unlimited?",
                ground_truth=(
                    "Roaming data passes have a fixed data allowance. "
                    "Check the Japan & Korea roaming pack details for the "
                    "exact data limit and daily rate."
                ),
            ),
        ],
    ),
]


# ===========================================================================
# PLAN RECOMMENDATION
# ===========================================================================

PLAN_CASES: list[EvalCase] = [
    # Casual
    EvalCase(
        question="what's a good plan for someone who streams a lot of netflix and youtube?",
        user_id="user_004",
        persona="casual",
        ground_truth=None,
    ),
    # Angry
    EvalCase(
        question=(
            "I was sold an 'unlimited' plan and now you're throttling my speed "
            "after 20GB. That is NOT unlimited. This is false advertising and "
            "I want a plan that actually does what it says."
        ),
        user_id="user_004",
        persona="angry",
        ground_truth=(
            "Unlimited plans typically include a high-speed data cap after which "
            "speeds are reduced but data remains available. "
            "Review your plan's fair-use policy, or consider upgrading to a plan "
            "with a higher high-speed cap."
        ),
    ),
    # Chatty — family scenario
    EvalCase(
        question=(
            "Okay so here's the situation: it's me, my husband, and our three "
            "teenagers — so five lines. The kids stream constantly, my husband "
            "works from home and uses a hotspot sometimes, and we do one "
            "international trip a year, usually Europe. What would you recommend? "
            "We're currently paying about $180 a month and honestly that feels "
            "like a lot."
        ),
        user_id="user_004",
        persona="chatty",
        ground_truth=None,
    ),
    # Follow-up after getting a recommendation
    EvalCase(
        question="what's the cheapest plan that still includes hotspot?",
        user_id="user_004",
        persona="neutral",
        ground_truth=None,
    ),
]

PLAN_CONVERSATIONS: list[ConversationCase] = [
    ConversationCase(
        description="Customer narrowing down plan options through back-and-forth questions",
        user_id="user_conv_06",
        persona="casual",
        turns=[
            Turn(message="I want to switch to a better plan"),
            Turn(message="something that has hotspot included"),
            Turn(
                message="is there a cheaper option that still includes at least 10GB of hotspot?",
                ground_truth=None,
            ),
        ],
    ),
]


# ===========================================================================
# DEVICE / IOT
# ===========================================================================

DEVICE_CASES: list[EvalCase] = [
    # Casual
    EvalCase(
        question="hey my apple watch lost its cellular connection, how do I fix it?",
        user_id="user_005",
        persona="casual",
        ground_truth=(
            "Ensure your Apple Watch has an active cellular plan linked to your "
            "account. Try unpairing and re-pairing the watch to your iPhone, "
            "then re-activating the cellular plan in the Watch app."
        ),
    ),
    # Angry
    EvalCase(
        question=(
            "I have been trying to activate my new SIM for THREE HOURS. "
            "Your website keeps timing out, the app gives me error code 500, "
            "and your phone line has a 45-minute wait. "
            "This is a completely broken experience."
        ),
        user_id="user_005",
        persona="angry",
        ground_truth=(
            "SIM activation can take up to 24 hours. If you are receiving "
            "error 500, there may be a provisioning delay. "
            "Contact support directly to manually trigger activation."
        ),
    ),
    # Technical
    EvalCase(
        question=(
            "Trying to provision an eSIM on a Samsung Galaxy S24 Ultra. "
            "The QR code scan fails with error E-SIM-003 — profile download "
            "interrupted. IMEI is verified and the device is unlocked. "
            "Is there a known issue with this handset's eSIM stack?"
        ),
        user_id="user_005",
        persona="technical",
        ground_truth=(
            "eSIM error E-SIM-003 typically indicates a profile download failure, "
            "often due to a carrier server timeout. "
            "Contact support to re-generate the eSIM QR code and retry the "
            "download on a stable Wi-Fi connection."
        ),
    ),
    # Senior
    EvalCase(
        question=(
            "My grandson bought me a new phone for Christmas and I can't figure "
            "out how to put my number on it. The old phone still works but "
            "I want to use the new one. What do I need to do?"
        ),
        user_id="user_005",
        persona="senior",
        ground_truth=(
            "To move your number to a new phone, you need to transfer or "
            "activate a new SIM card. Visit a store or follow the online "
            "activation steps, and your number will be moved within a few hours."
        ),
    ),
]


# ===========================================================================
# EDGE / SOCIAL CASES
# ===========================================================================

EDGE_CASES: list[EvalCase] = [
    EvalCase(
        question="hello, I have a question about my account",
        user_id="user_001",
        persona="greeting",
        ground_truth=None,
    ),
    EvalCase(
        question="everything is just broken and I'm so frustrated I don't even know where to start",
        user_id="user_002",
        persona="vague-angry",
        ground_truth=None,
    ),
    EvalCase(
        question="I just wanted to say thank you, the agent last week was super helpful",
        user_id="user_003",
        persona="compliment",
        ground_truth=None,
    ),
    EvalCase(
        question=(
            "I've called three times this week about the same problem and "
            "nobody has fixed it. I want to speak to a manager."
        ),
        user_id="user_002",
        persona="escalation-request",
        ground_truth=None,
    ),
]


# ===========================================================================
# Flat exports
# ===========================================================================

EVAL_CASES: list[EvalCase] = (
    BILLING_CASES
    + CONNECTIVITY_CASES
    + ROAMING_CASES
    + PLAN_CASES
    + DEVICE_CASES
    + EDGE_CASES
)

CONVERSATION_CASES: list[ConversationCase] = (
    BILLING_CONVERSATIONS
    + CONNECTIVITY_CONVERSATIONS
    + ROAMING_CONVERSATIONS
    + PLAN_CONVERSATIONS
)
