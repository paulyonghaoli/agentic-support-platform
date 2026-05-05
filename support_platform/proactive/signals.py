from __future__ import annotations

# ---------------------------------------------------------------------------
# Proactive support signal detection
# ---------------------------------------------------------------------------
# Given synthetic account data, detects conditions that warrant proactive
# outreach before the user contacts support. Returns actionable suggestions.
# ---------------------------------------------------------------------------

_DATA_USAGE_THRESHOLD = 0.90  # 90% of monthly limit
_TRAVEL_DAYS_THRESHOLD = 14   # upcoming travel within 14 days


def detect_signals(account: dict) -> list[str]:
    """Return a list of proactive support suggestions for the account."""
    signals: list[str] = []

    signals.extend(_check_data_usage(account))
    signals.extend(_check_upcoming_travel(account))
    signals.extend(_check_repeated_tickets(account))
    signals.extend(_check_plan_mismatch(account))

    return signals


def _check_data_usage(account: dict) -> list[str]:
    used = account.get("monthly_data_used_gb", 0)
    limit = account.get("monthly_data_limit_gb", -1)

    if limit == -1 or limit == 0:
        return []

    ratio = used / limit
    if ratio >= _DATA_USAGE_THRESHOLD:
        pct = int(ratio * 100)
        overage = used > limit
        if overage:
            excess = round(used - limit, 1)
            return [
                f"Account has exceeded the {limit} GB data cap by {excess} GB this month. "
                f"Consider upgrading to a higher-data or unlimited plan to avoid overage charges ($15/GB)."
            ]
        return [
            f"Account has used {pct}% of the monthly {limit} GB data cap. "
            "Consider a plan upgrade before the cycle ends to avoid overage charges."
        ]
    return []


def _check_upcoming_travel(account: dict) -> list[str]:
    travel = account.get("upcoming_travel")
    if not travel:
        return []

    country = travel.get("country", "")
    days_away = travel.get("departure_days_from_now", 999)
    roaming_active = account.get("roaming_add_on_active", False)

    if days_away <= _TRAVEL_DAYS_THRESHOLD and not roaming_active:
        return [
            f"Upcoming trip to {country} in {days_away} day(s) detected, "
            "but no roaming add-on is active. "
            "Recommend activating a roaming add-on at least 24 hours before departure "
            "to avoid unexpected Day Pass charges ($10/day)."
        ]
    return []


def _check_repeated_tickets(account: dict) -> list[str]:
    tickets = account.get("connectivity_tickets_last_90d", 0)
    if tickets >= 3:
        return [
            f"Account has {tickets} connectivity tickets in the last 90 days. "
            "Pattern suggests a recurring issue — recommend proactive escalation to network team."
        ]
    return []


def _check_plan_mismatch(account: dict) -> list[str]:
    used = account.get("monthly_data_used_gb", 0)
    limit = account.get("monthly_data_limit_gb", -1)
    current_plan = account.get("current_plan", "")

    if limit == -1:
        # Unlimited plan — check for under-usage (potential downgrade)
        if used < 5 and "unlimited" in current_plan:
            return [
                f"Account is on an unlimited plan but has only used {used} GB this month. "
                "A lower-tier plan may provide equivalent coverage at reduced cost."
            ]
        return []

    # Capped plan — check for consistent over-usage suggesting upgrade
    if used > limit * 0.95 and "basic" in current_plan:
        return [
            f"Account is consistently near or over its {limit} GB cap on the {current_plan} plan. "
            "Upgrading to Standard 20GB or higher would reduce overage risk."
        ]

    return []
