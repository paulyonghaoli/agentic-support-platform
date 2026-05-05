"""Shared fixtures for the test suite."""
from __future__ import annotations

import pytest

from support_platform.data.loaders import DataStore
from support_platform.agents.retrieval_agent import RetrievalAgent


@pytest.fixture(scope="session")
def data_store() -> DataStore:
    return DataStore()


@pytest.fixture(scope="session")
def retrieval_agent(data_store) -> RetrievalAgent:
    return RetrievalAgent(data_store)


@pytest.fixture
def demo_account_001(data_store) -> dict:
    return data_store.get_account("demo_user_001")


@pytest.fixture
def demo_account_002(data_store) -> dict:
    return data_store.get_account("demo_user_002")


@pytest.fixture
def demo_account_003(data_store) -> dict:
    return data_store.get_account("demo_user_003")


@pytest.fixture
def demo_account_004(data_store) -> dict:
    return data_store.get_account("demo_user_004")


@pytest.fixture
def demo_account_005(data_store) -> dict:
    return data_store.get_account("demo_user_005")
