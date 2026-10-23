"""Tests for the deterministic baseline schedule builder."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from build_baseline_schedule import build_schedule


def test_build_schedule_uses_age_offsets(tmp_path: Path) -> None:
    """A block reaches the target age after the difference in years."""
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    pd.DataFrame(
        {
            "block_id": [1, 1, 2],
            "track_id": [10, 11, 12],
            "offset": [20, 20, 80],
            "area_ha": [5.0, 2.0, 9.0],
        }
    ).to_parquet(dataset / "blocks.parquet", index=False)

    schedule, summary = build_schedule(
        dataset=dataset,
        target_age=60,
        treatment="CC",
    )

    assert schedule.to_dict("records") == [
        {"block_id": 1, "treatment": "CC", "offset": 40},
        {"block_id": 2, "treatment": "CC", "offset": 0},
    ]
    assert summary["block_count"] == 2
    assert summary["area_ha"] == 16.0
    assert summary["offset_min"] == 0
    assert summary["offset_max"] == 40


def test_build_schedule_rejects_missing_columns(tmp_path: Path) -> None:
    """A dataset without the required block and age columns is rejected."""
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    pd.DataFrame({"block_id": [1]}).to_parquet(dataset / "blocks.parquet", index=False)

    with pytest.raises(ValueError, match="missing columns"):
        build_schedule(dataset=dataset, target_age=60, treatment="CC")


def test_build_schedule_rejects_non_positive_target_age(tmp_path: Path) -> None:
    """The target age must be positive."""
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    pd.DataFrame(
        {
            "block_id": [1],
            "track_id": [10],
            "offset": [0],
            "area_ha": [1.0],
        }
    ).to_parquet(dataset / "blocks.parquet", index=False)

    with pytest.raises(ValueError, match="target_age"):
        build_schedule(dataset=dataset, target_age=0, treatment="CC")
