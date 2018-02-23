"""Pytest fixtures for testing."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()
