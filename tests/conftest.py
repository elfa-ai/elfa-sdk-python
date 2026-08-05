"""Shared test fixtures."""

import pytest

BASE_URL = "https://api.test.elfa.ai"


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def base_url():
    return BASE_URL
