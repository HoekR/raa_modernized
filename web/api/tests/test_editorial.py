"""Editorial amendment API tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from raa_api.auth import require_editor
from raa_api.config import EditorialSettings
from raa_api.editorial import sanitize_html


def _settings(**kwargs) -> EditorialSettings:
    base = EditorialSettings(
        enabled=True,
        api_key="test-secret",
        editor_id="editor",
        cors_origins=("http://localhost:5174",),
    )
    return EditorialSettings(**{**base.__dict__, **kwargs})


def test_sanitize_html_strips_script():
    raw = '<p>Hello</p><script>alert(1)</script>'
    clean = sanitize_html(raw)
    assert "<script>" not in clean
    assert "Hello" in clean


@patch("raa_api.auth.editorial_settings", return_value=_settings(enabled=False, api_key=""))
def test_require_editor_disabled(_mock):
    with pytest.raises(HTTPException) as exc:
        require_editor(x_editorial_api_key=None, authorization=None)
    assert exc.value.status_code == 503


@patch("raa_api.auth.editorial_settings", return_value=_settings())
def test_require_editor_valid_key(_mock):
    assert require_editor(x_editorial_api_key="test-secret", authorization=None) == "editor"


@patch("raa_api.editorial.nh3.clean", side_effect=lambda v, tags: v)
def test_upsert_amendment_calls_sanitize(_mock_clean):
    from raa_api.editorial import upsert_amendment

    db = MagicMock()
    db.execute.return_value.mappings.return_value.first.return_value = {
        "id": 1,
        "entity_type": "instelling",
        "entity_id": 42,
        "field": "toelichting",
        "value": "<p>x</p>",
        "editor_id": "editor",
        "note": None,
        "status": "active",
        "base_release_id": None,
        "created_at": None,
        "updated_at": None,
    }
    row = upsert_amendment(
        db,
        entity_type="instelling",
        entity_id=42,
        field="toelichting",
        value="<p>x</p>",
        editor_id="editor",
    )
    assert row["entity_id"] == 42
    assert db.commit.called
