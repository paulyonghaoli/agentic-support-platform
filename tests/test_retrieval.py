from __future__ import annotations

import pytest

from support_platform.schemas import Intent


def test_retrieval_returns_evidence_for_roaming(retrieval_agent):
    evidence = retrieval_agent.retrieve(Intent.ROAMING, "I'm traveling to Japan next week.")
    assert len(evidence) > 0
    ids = [e.id for e in evidence]
    assert any("roaming" in eid for eid in ids), f"Expected roaming evidence, got: {ids}"


def test_retrieval_returns_evidence_for_billing(retrieval_agent):
    evidence = retrieval_agent.retrieve(Intent.BILLING, "Why is my bill higher this month?")
    assert len(evidence) > 0
    ids = [e.id for e in evidence]
    assert any("billing" in eid for eid in ids), f"Expected billing evidence, got: {ids}"


def test_retrieval_returns_evidence_for_connectivity(retrieval_agent):
    evidence = retrieval_agent.retrieve(
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        "My data stopped working after changing plans.",
    )
    assert len(evidence) > 0
    ids = [e.id for e in evidence]
    assert any("trouble" in eid for eid in ids), f"Expected troubleshooting evidence, got: {ids}"


def test_retrieval_returns_evidence_for_device(retrieval_agent):
    evidence = retrieval_agent.retrieve(
        Intent.DEVICE_IOT_ACTIVATION,
        "My smartwatch is not connecting to cellular.",
    )
    assert len(evidence) > 0


def test_retrieval_relevance_scores_are_valid(retrieval_agent):
    evidence = retrieval_agent.retrieve(Intent.ROAMING, "traveling to Japan")
    for e in evidence:
        assert 0.0 <= e.relevance_score <= 1.0


def test_retrieval_evidence_has_required_fields(retrieval_agent):
    evidence = retrieval_agent.retrieve(Intent.BILLING, "bill is higher")
    for e in evidence:
        assert e.id
        assert e.source
        assert e.content
        assert e.relevance_score >= 0.0


def test_retrieve_plans_returns_all_plans(retrieval_agent):
    plans = retrieval_agent.retrieve_plans()
    assert len(plans) >= 5
    plan_ids = [p["plan_id"] for p in plans]
    assert "basic_5gb" in plan_ids
    assert "unlimited_plus" in plan_ids
    assert "family_unlimited" in plan_ids


def test_retrieve_plans_by_tag(retrieval_agent):
    family_plans = retrieval_agent.retrieve_plans(tags=["family"])
    assert all("family" in p.get("tags", []) for p in family_plans)
    assert len(family_plans) >= 2


def test_retrieve_account_returns_correct_account(retrieval_agent):
    account = retrieval_agent.retrieve_account("demo_user_001")
    assert account is not None
    assert account["user_id"] == "demo_user_001"
    assert "current_plan" in account


def test_retrieve_account_returns_none_for_unknown(retrieval_agent):
    account = retrieval_agent.retrieve_account("nonexistent_user_999")
    assert account is None


def test_retrieve_device_info_apple_watch(retrieval_agent):
    device = retrieval_agent.retrieve_device_info("Apple Watch Series 8")
    assert device is not None
    assert device.get("esim") is True


def test_evidence_capped_at_five_results(retrieval_agent):
    evidence = retrieval_agent.retrieve(Intent.BILLING, "bill charge payment invoice fee refund dispute")
    assert len(evidence) <= 5
