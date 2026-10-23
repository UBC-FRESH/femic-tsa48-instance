"""Tests for the public data manifest checker."""

from __future__ import annotations

from pathlib import Path

import pytest

from check_public_data import REQUIRED_PATHS, check_public_data


def _make_gdb(root: Path, relative: str) -> None:
    path = root / relative
    path.mkdir(parents=True)
    (path / "a00000001.gdbtable").write_bytes(b"key-table")
    (path / "a00000002.gdbtable").write_bytes(b"payload")


def test_check_public_data_records_each_required_gdb(tmp_path: Path) -> None:
    """Every required geodatabase is checked and hashed."""
    for relative in REQUIRED_PATHS:
        _make_gdb(tmp_path, relative)

    manifest = check_public_data(tmp_path)

    assert manifest["root"] == "${FEMIC_EXTERNAL_DATA_ROOT}"
    entries = manifest["entries"]
    assert isinstance(entries, list)
    assert len(entries) == len(REQUIRED_PATHS)
    assert entries[0]["key_table_bytes"] == 9
    assert isinstance(entries[0]["key_table_sha256"], str)


def test_check_public_data_rejects_missing_path(tmp_path: Path) -> None:
    """A missing geodatabase fails the check."""
    with pytest.raises(FileNotFoundError, match="missing public data path"):
        check_public_data(tmp_path, hashes=False)


def test_check_public_data_rejects_missing_key_table(tmp_path: Path) -> None:
    """A directory without the key table fails the check."""
    path = tmp_path / REQUIRED_PATHS[0]
    path.mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="missing key table"):
        check_public_data(tmp_path, hashes=False)
