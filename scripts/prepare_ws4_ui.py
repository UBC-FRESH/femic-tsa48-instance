#!/usr/bin/env python3
"""Prepare block geometry for the ws4 web UI from FEMIC fragment geometry.

FEMIC exports one polygon per fragment. The ws4 dataset keys its schedule by
block, so the UI geometry is dissolved to one feature per block and carries a
``block_id`` field that matches ``blocks.parquet``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


def _block_column(frame: gpd.GeoDataFrame) -> str:
    for candidate in ("BLOCK", "block", "block_id", "BLOCK_ID"):
        if candidate in frame.columns:
            return candidate
    raise ValueError("fragment geometry needs one of BLOCK, block, block_id, or BLOCK_ID")


def _round_coordinates(value: object, precision: int) -> object:
    """Round nested coordinate values to a fixed number of decimal places."""
    if isinstance(value, (list, tuple)):
        return [_round_coordinates(item, precision) for item in value]
    if isinstance(value, float):
        return round(value, precision)
    return value


def prepare_ui_geometry(
    *,
    fragments: Path,
    out: Path,
    simplify_m: float = 0.0,
    precision: int = 1,
    parts: Path | None = None,
) -> dict[str, object]:
    """Dissolve fragment geometry to blocks and write a GeoJSON file.

    Parameters
    ----------
    fragments : Path
        Fragment shapefile or GeoPackage exported by FEMIC.
    out : Path
        Destination GeoJSON path.
    simplify_m : float
        Douglas-Peucker tolerance in metres. The default 100 m is invisible at
        provincial map scales and keeps the browser payload small.
    precision : int
        Decimal places retained for native-CRS coordinates.
    parts : Path, optional
        A ``block_parts.csv`` sidecar with ``block_id``, ``part``, and ``k3z``.
        When given, the properties travel into the UI GeoJSON.

    Returns
    -------
    dict
        A JSON-ready summary with the source, block count, CRS, and tolerance.
    """
    frame = gpd.read_file(fragments)
    if frame.empty:
        raise ValueError(f"fragment geometry is empty: {fragments}")
    block_column = _block_column(frame)
    frame[block_column] = frame[block_column].astype(int)
    blocks = frame[[block_column, "geometry"]].dissolve(by=block_column).reset_index()
    blocks = blocks.rename(columns={block_column: "block_id"})
    blocks["block_id"] = blocks["block_id"].astype(int)
    if parts is not None and parts.exists():
        flags = pd.read_csv(parts)
        blocks = blocks.merge(flags[["block_id", "part", "k3z"]], on="block_id", how="left")
        blocks["part"] = blocks["part"].fillna("unknown").astype(str)
        blocks["k3z"] = blocks["k3z"].fillna(0).astype(int)
    if simplify_m > 0:
        blocks["geometry"] = blocks.geometry.simplify(simplify_m, preserve_topology=True)
    properties = ["block_id"]
    if parts is not None and parts.exists():
        properties.extend(["part", "k3z"])
    collection = blocks[[*properties, "geometry"]].__geo_interface__
    for feature in collection["features"]:
        feature["geometry"]["coordinates"] = _round_coordinates(
            feature["geometry"]["coordinates"], precision
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(collection, separators=(",", ":")), encoding="utf-8")
    return {
        "source": str(fragments),
        "out": str(out),
        "block_count": len(blocks),
        "crs": str(frame.crs) if frame.crs is not None else None,
        "simplify_m": simplify_m,
        "bytes": out.stat().st_size,
    }


def main() -> None:
    """Write the UI geometry and print its summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--simplify-m", type=float, default=0.0)
    parser.add_argument("--precision", type=int, default=1)
    parser.add_argument("--parts", type=Path, default=None)
    args = parser.parse_args()
    summary = prepare_ui_geometry(
        fragments=args.fragments,
        out=args.out,
        simplify_m=args.simplify_m,
        precision=args.precision,
        parts=args.parts,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
