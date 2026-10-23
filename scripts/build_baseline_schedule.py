#!/usr/bin/env python3
"""Build a deterministic baseline harvest schedule from a ws4 dataset.

Every block is harvested once with the declared treatment when it reaches the
target age. The schedule is keyed by the 0-based treatment ``offset``: offset 0
is the first simulation year, and a block already at or beyond the target age is
entered at offset 0. Period 0 is the zero-length pre-simulation snapshot and is
never a treatment slot. The schedule is deliberately simple: it gives the web UI
and the target reports a reproducible baseline before any optimizer run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def build_schedule(
    *,
    dataset: Path,
    target_age: int,
    treatment: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return a block schedule and a compact summary.

    Parameters
    ----------
    dataset : Path
        Compiled ws4 dataset directory containing ``blocks.parquet``.
    target_age : int
        Age in years at which each block is harvested.
    treatment : str
        Treatment code to apply, normally ``CC``.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The schedule with ``block_id``, ``treatment``, and ``period`` columns,
        and a JSON-ready summary.
    """
    blocks = pd.read_parquet(dataset / "blocks.parquet")
    required = {"block_id", "offset", "area_ha"}
    missing = required.difference(blocks.columns)
    if missing:
        raise ValueError(f"blocks.parquet is missing columns: {sorted(missing)}")
    if target_age <= 0:
        raise ValueError("target_age must be positive")

    grouped = (
        blocks.groupby("block_id", as_index=False)
        .agg(offset=("offset", "min"), area_ha=("area_ha", "sum"))
        .sort_values("block_id")
    )
    # Offset 0 is the first simulation year. Period 0 is the zero-length
    # snapshot before it, so a mature stand enters at offset 0.
    grouped["offset"] = (target_age - grouped["offset"]).clip(lower=0).astype(int)
    grouped["treatment"] = treatment
    schedule = grouped.loc[:, ["block_id", "treatment", "offset"]].copy()
    schedule["block_id"] = schedule["block_id"].astype(int)

    summary: dict[str, object] = {
        "dataset": str(dataset),
        "target_age": target_age,
        "treatment": treatment,
        "block_count": len(schedule),
        "area_ha": round(float(grouped["area_ha"].sum()), 4),
        "offset_min": int(schedule["offset"].min()),
        "offset_max": int(schedule["offset"].max()),
    }
    return schedule, summary


def main() -> None:
    """Write the baseline schedule and its summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--target-age", type=int, default=60)
    parser.add_argument("--treatment", default="CC")
    args = parser.parse_args()

    schedule, summary = build_schedule(
        dataset=args.dataset,
        target_age=args.target_age,
        treatment=args.treatment,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(args.out, index=False)
    summary_path = args.out.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
