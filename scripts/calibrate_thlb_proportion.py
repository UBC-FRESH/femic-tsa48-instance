#!/usr/bin/env python3
"""Calibrate per-stand THLB proportion to a target THLB area.

The legacy ``thlb_raw`` signal is a 0-100 per-stand THLB proportion. The full
TSA 48 checkpoint sums to 130,481.59 ha of managed area, while the reviewed TSR
reference is 177,505 ha. This script scales the per-stand proportion by a
single factor, caps it at 1.0, and writes a checkpoint copy with a new
``thlb_raw_calibrated`` column. The factor is solved so the capped proportional
area matches the target as closely as the data allow.

This is a reviewed calibration, not a replacement for the TSR netdown. It is
recorded in a summary JSON next to the calibrated checkpoint.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather


def _solve_factor(area_ha: np.ndarray, share: np.ndarray, target_ha: float) -> float:
    """Return the factor that makes the capped proportional area hit the target."""
    low, high = 0.0, 10.0
    for _ in range(100):
        mid = (low + high) / 2.0
        achieved = float((area_ha * np.clip(share * mid, 0.0, 1.0)).sum())
        if achieved < target_ha:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def main() -> None:
    """Write the calibrated checkpoint and its summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--target-ha", type=float, default=177505.0)
    parser.add_argument("--out-checkpoint", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--source-column", default="thlb_raw")
    parser.add_argument("--calibrated-column", default="thlb_raw_calibrated")
    args = parser.parse_args()

    table = feather.read_table(args.checkpoint, memory_map=True)
    names = set(table.schema.names)
    for column in (args.source_column, "FEATURE_AREA_SQM"):
        if column not in names:
            raise ValueError(f"checkpoint is missing {column!r}")
    raw = np.asarray(table[args.source_column].to_numpy(zero_copy_only=False), dtype=float)
    area_ha = (
        np.asarray(table["FEATURE_AREA_SQM"].to_numpy(zero_copy_only=False), dtype=float) / 10000.0
    )
    raw = np.clip(np.nan_to_num(raw, nan=0.0), 0.0, 100.0)
    share = raw / 100.0

    base_area = float((area_ha * share).sum())
    factor = _solve_factor(area_ha, share, args.target_ha)
    calibrated_share = np.clip(share * factor, 0.0, 1.0)
    calibrated_area = float((area_ha * calibrated_share).sum())
    calibrated_raw = calibrated_share * 100.0
    saturated = int((share * factor > 1.0).sum())

    calibrated = pa.array(calibrated_raw.astype(np.float64))
    index = table.schema.get_field_index(args.calibrated_column)
    if index >= 0:
        table = table.set_column(index, args.calibrated_column, calibrated)
    else:
        table = table.append_column(args.calibrated_column, calibrated)
    args.out_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    feather.write_feather(table, args.out_checkpoint, compression="lz4")

    summary = {
        "checkpoint": str(args.checkpoint),
        "out_checkpoint": str(args.out_checkpoint),
        "source_column": args.source_column,
        "calibrated_column": args.calibrated_column,
        "target_ha": args.target_ha,
        "base_area_ha": round(base_area, 6),
        "factor": factor,
        "calibrated_area_ha": round(calibrated_area, 6),
        "target_error_ha": round(calibrated_area - args.target_ha, 6),
        "saturated_rows": saturated,
        "rows": int(table.num_rows),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
