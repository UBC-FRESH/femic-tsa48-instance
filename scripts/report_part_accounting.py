#!/usr/bin/env python3
"""Combine the full, NICC, and outside runs into one part-level accounting table.

The full TSA 48 model carries a ``part`` flag. Running the same dataset with the
full, NICC-only, and outside-only schedules gives three account series that
reconcile exactly because ws4 simulation is linear in scheduled blocks. This
script writes the combined table and a reconciliation check so the NICC subset
can be isolated in accounting.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    """Write the combined part accounting table and reconciliation report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    frames: list[pd.DataFrame] = []
    for part in ("full", "nicc", "outside"):
        path = args.runs / part / "account_values.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        frame.insert(0, "part", part)
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.out, index=False)

    pivot = combined.pivot_table(
        index=["offset", "account"], columns="part", values="value", aggfunc="sum"
    ).reset_index()
    for column in ("full", "nicc", "outside"):
        if column not in pivot.columns:
            pivot[column] = 0.0
    pivot["nicc_plus_outside"] = pivot["nicc"] + pivot["outside"]
    pivot["reconciliation_error"] = (pivot["full"] - pivot["nicc_plus_outside"]).abs()
    pivot.to_csv(args.out.with_name(args.out.stem + "_reconciliation.csv"), index=False)
    report = {
        "rows": len(pivot),
        "max_reconciliation_error": float(pivot["reconciliation_error"].max()),
        "max_reconciliation_error_account": (
            str(pivot.sort_values("reconciliation_error").iloc[-1]["account"])
            if len(pivot)
            else None
        ),
        "combined": str(args.out),
        "reconciliation": str(args.out.with_name(args.out.stem + "_reconciliation.csv")),
    }
    args.out.with_suffix(".summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
