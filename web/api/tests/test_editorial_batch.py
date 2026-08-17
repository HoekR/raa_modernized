"""Batch editorial API tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from raa_api.editorial_batch import apply_batch_changes, fetch_batch_rows


def test_fetch_batch_rows_rejects_unknown_entity():
    db = MagicMock()
    with pytest.raises(ValueError, match="Unknown entity"):
        fetch_batch_rows(db, "nope", [1])


def test_fetch_batch_rows_rejects_unknown_field():
    db = MagicMock()
    with pytest.raises(ValueError, match="not allowed"):
        fetch_batch_rows(db, "persoon", [1], fields=["toelichting"])


@patch("raa_api.editorial_batch.get_active_amendment", return_value=None)
@patch("raa_api.editorial_batch.refresh_persoon_derived")
@patch("raa_api.editorial_batch.upsert_amendment")
def test_apply_batch_skips_unchanged(mock_upsert, mock_refresh, _mock_amend):
    db = MagicMock()
    db.execute.return_value.mappings.return_value.first.return_value = {
        "id": 1,
        "geslachtsnaam": "Janssen",
        "import_release_id": "dev",
    }
    result = apply_batch_changes(
        db,
        changes=[
            {
                "entity_type": "persoon",
                "entity_id": 1,
                "field": "geslachtsnaam",
                "value": "Janssen",
            }
        ],
        editor_id="editor",
    )
    assert len(result["skipped"]) == 1
    mock_upsert.assert_not_called()
    mock_refresh.assert_not_called()


@patch("raa_api.editorial_batch.get_active_amendment", return_value=None)
@patch("raa_api.editorial_batch.refresh_persoon_derived")
@patch("raa_api.editorial_batch.upsert_amendment", return_value={"id": 9})
def test_apply_batch_applies_change(mock_upsert, mock_refresh, _mock_amend):
    db = MagicMock()
    db.execute.return_value.mappings.return_value.first.return_value = {
        "id": 1,
        "geboortejaar": "2001",
        "import_release_id": "dev",
    }
    result = apply_batch_changes(
        db,
        changes=[
            {
                "entity_type": "persoon",
                "entity_id": 1,
                "field": "geboortejaar",
                "value": "1720",
            }
        ],
        editor_id="editor",
    )
    assert len(result["applied"]) == 1
    mock_upsert.assert_called_once()
    mock_refresh.assert_called_once_with(db, 1, commit=False)
    db.commit.assert_called_once()


@patch(
    "raa_api.editorial_batch.get_active_amendment",
    return_value={"id": 3, "value": "1720"},
)
@patch("raa_api.editorial_batch.refresh_persoon_derived")
@patch("raa_api.editorial_batch.revert_amendment", return_value={"id": 3})
def test_apply_batch_reverts_to_base(mock_revert, mock_refresh, _mock_amend):
    db = MagicMock()
    db.execute.return_value.mappings.return_value.first.return_value = {
        "id": 1,
        "geboortejaar": "2001",
        "import_release_id": "dev",
    }
    result = apply_batch_changes(
        db,
        changes=[
            {
                "entity_type": "persoon",
                "entity_id": 1,
                "field": "geboortejaar",
                "value": "2001",
            }
        ],
        editor_id="editor",
    )
    assert len(result["reverted"]) == 1
    mock_revert.assert_called_once_with(db, 3, commit=False)
    mock_refresh.assert_called_once_with(db, 1, commit=False)
