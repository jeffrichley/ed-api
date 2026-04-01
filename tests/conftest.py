"""Shared test fixtures for ed-api tests."""

import json
import pathlib
from unittest.mock import AsyncMock, MagicMock

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures" / "responses"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def user_info_response() -> dict:
    return load_fixture("user_info.json")


@pytest.fixture
def thread_list_response() -> dict:
    return load_fixture("thread_list.json")


@pytest.fixture
def thread_detail_response() -> dict:
    return load_fixture("thread_detail.json")


@pytest.fixture
def comment_response() -> dict:
    return load_fixture("comment.json")


@pytest.fixture
def file_upload_response() -> dict:
    return load_fixture("file_upload.json")
