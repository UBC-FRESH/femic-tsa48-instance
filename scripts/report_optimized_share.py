#!/usr/bin/env python3
"""Report the NICC share of an optimized full-TSA schedule.

The full, NICC-only, and outside-only optimized runs use the same dataset and
the same schedule, filtered by part. This script reports the harvest shares that
the NICC-overlap model can use as a reference when the full model is
benchmarked against the published AAC.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

AAC_M3_PER_YEAR = 1_248_100.0
HARVEST_ACCOUNT = "product.Yield.managed.Total"


def _harvest(run: Path) -> dict[str, float]:
    """Return year-zero, first-decade, and total harvest for one run."""
    values = pd.read_csv(run / "account_values.csv")
    rows = values[values["account"].astype(str) == HARVEST_ACCOUNT]
    annual = rows.groupby("offset")["value"].sum().sort_index()
    return {
        "snapshot_m3": float(annual.get(-1, 0.0)),
        "first_decade_m3": float(annual.loc[(annual.index >= 0) & (annual.index <= 9)].sum()),
        "total_m3": float(annual.sum()),
    }


def main() -> None:
    """Write the optimized part-share evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    parts = {
        part: _harvest(args.runs / f"optimized_{part}") for part in ("full", "nicc", "outside")
    }
    full = parts["full"]
    nicc = parts["nicc"]
    payload = {
        "runs": parts,
        "nicc_share_first_decade": nicc["first_decade_m3"] / full["first_decade_m3"]
        if full["first_decade_m3"]
        else 0.0,
        "nicc_share_total": nicc["total_m3"] / full["total_m3"] if full["total_m3"] else 0.0,
        "nicc_reference_aac_m3_per_year": (
            nicc["first_decade_m3"] / full["first_decade_m3"] * AAC_M3_PER_YEAR
            if full["first_decade_m3"]
            else 0.0
        ),
        "aac_m3_per_year": AAC_M3_PER_YEAR,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    frame = pd.DataFrame(
        [
            {
                "part": part,
                **values,
                "share_first_decade": values["first_decade_m3"] / full["first_decade_m3"]
                if full["first_decade_m3"]
                else 0.0,
                "share_total": values["total_m3"] / full["total_m3"] if full["total_m3"] else 0.0,
            }
            for part, values in parts.items()
        ]
    )
    frame.to_csv(args.out.with_suffix(".csv"), index=False)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
