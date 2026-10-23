#!/usr/bin/env python3
"""Create NICC-only and outside-only accounting views of the full TSA dataset.

WS4 reports state/area accounts over the dataset's fragments, not over the
scheduled blocks. To isolate the NICC part exactly in every account, the full
dataset is copied and its fragment/block tables are filtered to the part. The
tracks, curves, treatments, and products are unchanged; the filtered dataset is
still a valid ws4 matrix, and the original full dataset keeps its part flags.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


def _copy_dataset(source: Path, target: Path) -> None:
    """Copy a compiled dataset directory."""
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _filter_dataset(dataset: Path, flags: pd.DataFrame, part: str) -> dict[str, object]:
    """Filter one dataset copy to a part and return a summary."""
    blocks_path = dataset / "blocks.parquet"
    fragments_path = dataset / "fragments.parquet"
    blocks = pd.read_parquet(blocks_path)
    fragments = pd.read_parquet(fragments_path)
    keep = set(flags.loc[flags["part"].astype(str) == part, "block_id"].astype(int))
    blocks = blocks[blocks["block_id"].astype(int).isin(keep)].copy()
    fragments = fragments[fragments["block_id"].astype(int).isin(keep)].copy()
    if blocks.empty:
        # An empty part is a legitimate edge case for a test subset; write the
        # empty tables so downstream steps can still run.
        blocks.to_parquet(blocks_path, index=False)
        fragments.to_parquet(fragments_path, index=False)
        return {
            "part": part,
            "dataset": str(dataset),
            "blocks": 0,
            "fragments": 0,
            "area_ha": 0.0,
        }
    blocks.to_parquet(blocks_path, index=False)
    fragments.to_parquet(fragments_path, index=False)
    return {
        "part": part,
        "dataset": str(dataset),
        "blocks": len(blocks),
        "fragments": len(fragments),
        "area_ha": round(float(fragments["area_ha"].sum()), 4),
    }


def main() -> None:
    """Write the part datasets and print their summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--parts", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    flags = pd.read_csv(args.parts)
    if not {"block_id", "part"}.issubset(flags.columns):
        raise ValueError("parts CSV needs block_id and part columns")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for part in ("nicc", "outside"):
        target = args.out_dir / f"matrix_{part}"
        _copy_dataset(args.dataset, target)
        summaries.append(_filter_dataset(target, flags, part))
    (args.out_dir / "part_datasets.summary.json").write_text(
        json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
