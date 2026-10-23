#!/usr/bin/env python3
"""Flag full-TSA blocks by the NICC overlap and the K3Z community forest.

The full TSA 48 model is one dataset. The NICC district intersection and the
K3Z community forest are spatial flags on its blocks, so the same model can be
reported as the whole TSA, the NICC overlap, the remainder, or K3Z.

The script writes a sidecar block table and, when ``--dataset`` is given, adds
the same columns to the compiled ws4 ``blocks.parquet`` and
``fragments.parquet``. WS4 ignores unknown columns during simulation, and the
schema validator accepts them, so the flags travel with the dataset without
changing the model mathematics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


def _block_column(frame: gpd.GeoDataFrame) -> str:
    """Return the fragment block-id column name."""
    for candidate in ("BLOCK", "block", "block_id", "BLOCK_ID"):
        if candidate in frame.columns:
            return candidate
    raise ValueError("fragment geometry needs one of BLOCK, block, block_id, or BLOCK_ID")


def _flag_frame(
    fragments: gpd.GeoDataFrame,
    block_column: str,
    nicc: gpd.GeoDataFrame,
    k3z: gpd.GeoDataFrame | None,
) -> pd.DataFrame:
    """Return one row per block with ``part`` and ``k3z`` flags."""
    frame = fragments[[block_column, "geometry"]].copy()
    frame[block_column] = frame[block_column].astype(int)
    if frame.crs is None:
        raise ValueError("fragment geometry has no CRS")
    if nicc.crs is not None and nicc.crs != frame.crs:
        nicc = nicc.to_crs(frame.crs)
    if k3z is not None and k3z.crs is not None and k3z.crs != frame.crs:
        k3z = k3z.to_crs(frame.crs)

    nicc_blocks = set(
        gpd.sjoin(
            frame,
            nicc[["geometry"]],
            how="inner",
            predicate="intersects",
        )[block_column].astype(int)
    )
    k3z_blocks: set[int] = set()
    if k3z is not None and not k3z.empty:
        k3z_blocks = set(
            gpd.sjoin(
                frame,
                k3z[["geometry"]],
                how="inner",
                predicate="intersects",
            )[block_column].astype(int)
        )

    rows: list[dict[str, object]] = []
    for block_id, group in frame.groupby(block_column, sort=True):
        block_id = int(block_id)
        rows.append(
            {
                "block_id": block_id,
                "part": "nicc" if block_id in nicc_blocks else "outside",
                "k3z": 1 if block_id in k3z_blocks else 0,
                "area_ha": round(float(group.geometry.area.sum()) / 10000.0, 6),
            }
        )
    return pd.DataFrame(rows)


def _apply_to_dataset(dataset: Path, flags: pd.DataFrame) -> None:
    """Add the flags to a compiled ws4 dataset's block and fragment tables."""
    blocks_path = dataset / "blocks.parquet"
    fragments_path = dataset / "fragments.parquet"
    blocks = pd.read_parquet(blocks_path)
    fragments = pd.read_parquet(fragments_path)
    part = flags[["block_id", "part", "k3z"]]
    blocks = blocks.drop(columns=["part", "k3z"], errors="ignore").merge(
        part, on="block_id", how="left"
    )
    fragments = fragments.drop(columns=["part", "k3z"], errors="ignore").merge(
        part, on="block_id", how="left"
    )
    if blocks["part"].isna().any() or fragments["part"].isna().any():
        raise ValueError("some dataset blocks have no part flag")
    blocks["part"] = blocks["part"].astype("string")
    fragments["part"] = fragments["part"].astype("string")
    blocks["k3z"] = blocks["k3z"].fillna(0).astype("int64")
    fragments["k3z"] = fragments["k3z"].fillna(0).astype("int64")
    blocks.to_parquet(blocks_path, index=False)
    fragments.to_parquet(fragments_path, index=False)


def main() -> None:
    """Flag blocks, write the sidecar table, and update the dataset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--nicc", type=Path, required=True)
    parser.add_argument("--k3z", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=None)
    args = parser.parse_args()

    fragments = gpd.read_file(args.fragments)
    if fragments.empty:
        raise ValueError(f"fragment geometry is empty: {args.fragments}")
    nicc = gpd.read_file(args.nicc)
    k3z = gpd.read_file(args.k3z) if args.k3z is not None and args.k3z.exists() else None
    block_column = _block_column(fragments)
    flags = _flag_frame(fragments, block_column, nicc, k3z)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    flags.to_csv(args.out_dir / "block_parts.csv", index=False)
    if args.dataset is not None:
        _apply_to_dataset(args.dataset, flags)
    summary = {
        "fragments": str(args.fragments),
        "block_column": block_column,
        "block_count": len(flags),
        "nicc_blocks": int((flags["part"] == "nicc").sum()),
        "outside_blocks": int((flags["part"] == "outside").sum()),
        "k3z_blocks": int((flags["k3z"] == 1).sum()),
        "nicc_area_ha": round(float(flags.loc[flags["part"] == "nicc", "area_ha"].sum()), 4),
        "outside_area_ha": round(float(flags.loc[flags["part"] == "outside", "area_ha"].sum()), 4),
        "k3z_area_ha": round(float(flags.loc[flags["k3z"] == 1, "area_ha"].sum()), 4),
        "block_parts": str(args.out_dir / "block_parts.csv"),
        "dataset": str(args.dataset) if args.dataset is not None else None,
    }
    (args.out_dir / "block_parts.summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
