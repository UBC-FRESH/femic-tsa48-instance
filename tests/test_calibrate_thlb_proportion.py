"""Tests for the per-stand THLB proportion calibration script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pytest

from calibrate_thlb_proportion import _solve_factor, main


def _write_checkpoint(path: Path, raw: list[float], area_m2: list[float]) -> None:
    """Write a minimal checkpoint with the calibration inputs."""
    table = pa.table(
        {
            "thlb_raw": pa.array(raw, type=pa.float64()),
            "FEATURE_AREA_SQM": pa.array(area_m2, type=pa.float64()),
        }
    )
    feather.write_feather(table, path)


def test_solve_factor_hits_a_reachable_target() -> None:
    """The solved factor makes the capped proportional area match the target."""
    area_ha = np.array([10.0, 20.0, 30.0, 40.0])
    share = np.array([0.0, 0.25, 0.5, 1.0])
    target = float((area_ha * share).sum()) * 1.5

    factor = _solve_factor(area_ha, share, target)
    achieved = float((area_ha * np.clip(share * factor, 0.0, 1.0)).sum())

    assert achieved == pytest.approx(target, abs=1e-6)


def test_main_writes_a_calibrated_checkpoint_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI entry point scales the raw signal and records the factor."""
    checkpoint = tmp_path / "checkpoint.feather"
    _write_checkpoint(checkpoint, raw=[0.0, 25.0, 50.0, 100.0], area_m2=[100_000.0] * 4)
    out_checkpoint = tmp_path / "calibrated.feather"
    summary_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "calibrate_thlb_proportion.py",
            "--checkpoint",
            str(checkpoint),
            "--target-ha",
            "20",
            "--out-checkpoint",
            str(out_checkpoint),
            "--summary",
            str(summary_path),
        ],
    )

    main()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["target_ha"] == 20.0
    assert summary["calibrated_area_ha"] == pytest.approx(20.0, abs=1e-6)
    calibrated = feather.read_table(out_checkpoint).to_pandas()
    assert calibrated["thlb_raw_calibrated"].max() <= 100.0
    assert calibrated["thlb_raw_calibrated"].tolist()[0] == 0.0
