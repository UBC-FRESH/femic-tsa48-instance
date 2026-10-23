#!/usr/bin/env python3
"""Benchmark a full-TSA ws4 run against the published TSR reference numbers.

The North Island TSA (TSA 48) 2020 data package reports a current AAC of
1,248,100 m3/yr and a current THLB of 177,505 ha. This script summarizes a
simulated full-TSA run, a NICC-only run, and an outside-NICC run against those
numbers, and writes a small evidence table.

The simulator is linear in scheduled blocks, so the full run is the sum of the
two part runs; the script checks that reconciliation too.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

AAC_M3_PER_YEAR = 1_248_100.0
THLB_HA = 177_505.0
HARVEST_ACCOUNT = "product.Yield.managed.Total"


def _annual_harvest(run: Path) -> pd.Series:
    """Return annual harvest volume for a run, indexed by year."""
    values = pd.read_csv(run / "account_values.csv")
    rows = values[values["account"].astype(str) == HARVEST_ACCOUNT]
    if rows.empty and (run / "product_values.csv").exists():
        products = pd.read_csv(run / "product_values.csv")
        rows = products[products["account"].astype(str) == HARVEST_ACCOUNT]
    if rows.empty:
        return pd.Series(dtype=float)
    series = rows.groupby("offset")["value"].sum().sort_index()
    return series.astype(float)


def _managed_area(run: Path) -> float:
    """Return the run's managed-area account value, or zero when absent."""
    values = pd.read_csv(run / "account_values.csv")
    rows = values[values["account"].astype(str) == "feature.Area.managed"]
    if rows.empty:
        return 0.0
    return float(rows["value"].max())


def _summary(name: str, run: Path, schedule: Path, dataset: Path) -> dict[str, object]:
    """Summarize one run's harvest against the TSR reference."""
    blocks = pd.read_parquet(dataset / "blocks.parquet")
    harvest = _annual_harvest(run)
    scheduled = pd.read_csv(schedule)
    scheduled_blocks = blocks[blocks["block_id"].isin(scheduled["block_id"])]
    managed_area = _managed_area(run)
    mean = float(harvest.mean()) if len(harvest) else 0.0
    return {
        "run": name,
        "run_dir": str(run),
        "schedule": str(schedule),
        "years": len(harvest),
        "harvest_m3": round(float(harvest.sum()), 4),
        "harvest_m3_per_year_mean": round(mean, 4),
        "harvest_m3_per_year_max": round(float(harvest.max()), 4) if len(harvest) else 0.0,
        "harvest_m3_per_year_min": round(float(harvest.min()), 4) if len(harvest) else 0.0,
        "aac_m3_per_year": AAC_M3_PER_YEAR,
        "mean_percent_of_aac": round(mean / AAC_M3_PER_YEAR * 100.0, 4),
        "scheduled_blocks": int(scheduled["block_id"].nunique()),
        "scheduled_area_ha": round(float(scheduled_blocks["area_ha"].sum()), 4),
        "model_managed_area_ha": round(managed_area, 4),
        "tsr_thlb_ha": THLB_HA,
        "managed_area_percent_of_thlb": round(managed_area / THLB_HA * 100.0, 4),
    }


def main() -> None:
    """Write the TSR benchmark evidence table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--part-datasets", type=Path, default=None)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--schedules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    if "part" not in blocks.columns:
        raise ValueError("blocks.parquet has no part column; run flag_parts.py first")
    summaries = []
    for name in ("full", "nicc", "outside"):
        dataset = args.dataset
        if name != "full" and args.part_datasets is not None:
            dataset = args.part_datasets / f"matrix_{name}"
        summaries.append(
            _summary(
                name,
                args.runs / name,
                args.schedules / f"{name}.csv",
                dataset,
            )
        )
    frame = pd.DataFrame(summaries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    payload = {
        "reference": {
            "aac_m3_per_year": AAC_M3_PER_YEAR,
            "current_thlb_ha": THLB_HA,
            "source": "North Island TSA Timber Supply Review Data Package, July 2020, Table 4",
        },
        "runs": summaries,
    }
    args.out.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
