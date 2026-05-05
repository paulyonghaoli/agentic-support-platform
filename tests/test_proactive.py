from __future__ import annotations

import pytest

from support_platform.proactive.signals import detect_signals


def test_high_data_usage_triggers_signal(demo_account_001):
    # demo_user_001: used 4.8/5 GB (96%)
    signals = detect_signals(demo_account_001)
    assert any("data" in s.lower() and ("upgrade" in s.lower() or "cap" in s.lower()) for s in signals)


def test_data_overage_triggers_signal(demo_account_002):
    # demo_user_002: used 72.3/60 GB — over limit
    signals = detect_signals(demo_account_002)
    assert any("exceeded" in s.lower() or "overage" in s.lower() for s in signals)


def test_upcoming_travel_no_roaming_triggers_signal(demo_account_001):
    # demo_user_001: traveling to Japan in 7 days, no roaming add-on
    signals = detect_signals(demo_account_001)
    assert any("japan" in s.lower() or "roaming" in s.lower() for s in signals)


def test_no_upcoming_travel_no_travel_signal(demo_account_002):
    # demo_user_002: no upcoming travel
    signals = detect_signals(demo_account_002)
    travel_signals = [s for s in signals if "trip" in s.lower() or "travel" in s.lower()]
    assert len(travel_signals) == 0


def test_repeated_tickets_triggers_escalation_signal(demo_account_004):
    # demo_user_004: 4 connectivity tickets in 90 days
    signals = detect_signals(demo_account_004)
    assert any("ticket" in s.lower() or "connectivity" in s.lower() for s in signals)


def test_normal_user_no_signals(demo_account_003):
    # demo_user_003: only 3.1/20 GB used, no travel, no repeated tickets
    signals = detect_signals(demo_account_003)
    # Should not trigger data usage signals (usage ratio is low)
    data_signals = [s for s in signals if "data cap" in s.lower() or "exceeded" in s.lower()]
    assert len(data_signals) == 0


def test_signals_are_strings():
    account = {
        "user_id": "test",
        "monthly_data_used_gb": 4.9,
        "monthly_data_limit_gb": 5,
        "upcoming_travel": None,
        "connectivity_tickets_last_90d": 0,
        "current_plan": "basic_5gb",
        "roaming_add_on_active": False,
    }
    signals = detect_signals(account)
    for s in signals:
        assert isinstance(s, str)
        assert len(s) > 10


def test_unlimited_plan_no_data_overage_signal():
    account = {
        "user_id": "test",
        "monthly_data_used_gb": 60,
        "monthly_data_limit_gb": -1,
        "upcoming_travel": None,
        "connectivity_tickets_last_90d": 0,
        "current_plan": "unlimited_plus",
        "roaming_add_on_active": False,
    }
    signals = detect_signals(account)
    data_overage = [s for s in signals if "exceeded" in s.lower()]
    assert len(data_overage) == 0
