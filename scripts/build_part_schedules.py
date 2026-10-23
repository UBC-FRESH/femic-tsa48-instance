#!/usr/bin/env python3
"""Build full, NICC-only, and outside-NICC baseline schedules from one dataset.

The full TSA 48 dataset carries a ``part`` column on ``blocks.parquet``. This
script writes one deterministic clearcut-at-target-age schedule per part. The
simulator is linear in scheduled blocks, so the NICC and outside runs sum to
the full run; that is the accounting isolation the two-part model needs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def _schedule(blocks: pd.DataFrame, target_age: int, treatment: str) -> pd.DataFrame:
    """Return one schedule row per block."""
    grouped = (
        blocks.groupby("block_id", as_index=False)
        .agg(offset=("offset", "min"), area_ha=("area_ha", "sum"))
        .sort_values("block_id")
    )
    # Offset 0 is the first simulation year; period 0 is the zero-length
    # snapshot before it, so mature stands enter at offset 0.
    grouped["offset"] = (target_age - grouped["offset"]).clip(lower=0).astype(int)
    grouped["treatment"] = treatment
    return grouped.loc[:, ["block_id", "treatment", "offset"]].copy()


def _summary(
    name: str, schedule: pd.DataFrame, blocks: pd.DataFrame, target_age: int, treatment: str
) -> dict[str, object]:
    """Return a JSON-ready schedule summary."""
    area = float(blocks.loc[blocks["block_id"].isin(schedule["block_id"]), "area_ha"].sum())
    return {
        "part": name,
        "target_age": target_age,
        "treatment": treatment,
        "block_count": len(schedule),
        "area_ha": round(area, 4),
        "offset_min": int(schedule["offset"].min()) if len(schedule) else None,
        "offset_max": int(schedule["offset"].max()) if len(schedule) else None,
    }


def main() -> None:
    """Write the full, NICC, and outside schedules and their summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--target-age", type=int, default=60)
    parser.add_argument("--treatment", default="CC")
    args = parser.parse_args()

    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    required = {"block_id", "offset", "area_ha", "part"}
    missing = required.difference(blocks.columns)
    if missing:
        raise ValueError(f"blocks.parquet is missing columns: {sorted(missing)}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, object]] = []
    for name in ("full", "nicc", "outside"):
        selected = blocks if name == "full" else blocks[blocks["part"].astype(str) == name]
        schedule = _schedule(selected, args.target_age, args.treatment)
        path = args.out_dir / f"{name}.csv"
        schedule.to_csv(path, index=False)
        summary = _summary(name, schedule, selected, args.target_age, args.treatment)
        summaries.append(summary)
        (args.out_dir / f"{name}.summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    (args.out_dir / "parts.summary.json").write_text(
        json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
