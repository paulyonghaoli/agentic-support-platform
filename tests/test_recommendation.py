from __future__ import annotations

import pytest

from support_platform.agents.recommendation_agent import RecommendationAgent
from support_platform.schemas import Intent


@pytest.fixture
def agent() -> RecommendationAgent:
    return RecommendationAgent(client=None)


@pytest.fixture
def all_plans(data_store) -> list[dict]:
    return data_store.plans


def test_family_high_usage_recommends_family_unlimited(agent, all_plans, demo_account_002):
    result = agent.recommend(
        "My family uses around 80GB per month. Should we change plans?",
        Intent.PLAN_RECOMMENDATION,
        evidence=[],
        account=demo_account_002,
        plans=all_plans,
    )
    assert "family_unlimited" in result.recommended_option.lower()
    assert result.rationale
    assert len(result.limitations) > 0


def test_recommendation_includes_rationale(agent, all_plans):
    result = agent.recommend(
        "What's the best plan for moderate use?",
        Intent.PLAN_RECOMMENDATION,
        evidence=[],
        account=None,
        plans=all_plans,
    )
    assert result.rationale
    assert len(result.rationale) > 20


def test_recommendation_uses_plan_data(agent, all_plans):
    result = agent.recommend(
        "I need an unlimited data plan.",
        Intent.PLAN_RECOMMENDATION,
        evidence=[],
        account=None,
        plans=all_plans,
    )
    assert result.recommended_option
    plan_ids = [p["plan_id"] for p in all_plans]
    assert any(pid in result.recommended_option for pid in plan_ids)


def test_roaming_japan_recommends_japan_pack(agent, all_plans, demo_account_001):
    result = agent.recommend(
        "I'm traveling to Japan next week. What roaming option do I need?",
        Intent.ROAMING,
        evidence=[],
        account=demo_account_001,
        plans=all_plans,
    )
    assert "japan" in result.recommended_option.lower() or "roaming_japan" in result.recommended_option.lower()
    assert "japan" in result.rationale.lower()


def test_roaming_europe_recommends_europe_pack(agent, all_plans):
    result = agent.recommend(
        "I'm traveling to France and Germany next month.",
        Intent.ROAMING,
        evidence=[],
        account=None,
        plans=all_plans,
    )
    assert "europe" in result.recommended_option.lower() or "europe" in result.rationale.lower()


def test_recommendation_has_alternatives(agent, all_plans):
    result = agent.recommend(
        "Which plan is best for my family?",
        Intent.PLAN_RECOMMENDATION,
        evidence=[],
        account=None,
        plans=all_plans,
    )
    assert isinstance(result.alternatives, list)


def test_recommendation_has_evidence_ids(agent, all_plans):
    from support_platform.schemas import Evidence
    mock_evidence = [
        Evidence(id="roaming_japan_001", source="roaming_policies", content="Japan pack details", relevance_score=0.9)
    ]
    result = agent.recommend(
        "Traveling to Japan.",
        Intent.ROAMING,
        evidence=mock_evidence,
        account=None,
        plans=all_plans,
    )
    assert isinstance(result.evidence_ids, list)
