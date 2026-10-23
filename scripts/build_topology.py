#!/usr/bin/env python
"""Build the block adjacency topology for patch and spatial constraints.

The output uses the established ``BLOCK1,BLOCK2,DISTANCE,LENGTH`` contract. A
zero distance is a pair whose polygons touch; the shared boundary length is the
intersection length. The patch policy joins only touching blocks, so the default
threshold is 0 m.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.errors import GEOSException


def build_topology(
    *,
    fragments_path: Path,
    output_path: Path,
    distance_m: float,
) -> pd.DataFrame:
    """Write the proximal topology CSV for the block polygons.

    Parameters
    ----------
    fragments_path : Path
        Block GeoJSON/Shapefile with ``block_id`` or ``BLOCK``.
    output_path : Path
        Destination CSV.
    distance_m : float
        Maximum polygon-to-polygon distance for an edge.

    Returns
    -------
    pandas.DataFrame
        The edge list with ``BLOCK1``, ``BLOCK2``, ``DISTANCE`` and ``LENGTH``.
    """
    fragments = gpd.read_file(fragments_path)
    key_column = "block_id" if "block_id" in fragments.columns else "BLOCK"
    if key_column not in fragments.columns:
        raise SystemExit(f"{fragments_path} needs block_id or BLOCK")
    fragments = fragments.loc[
        fragments.geometry.notna() & ~fragments.geometry.is_empty
    ].reset_index(drop=True)
    keys = fragments[key_column].astype(int).to_numpy()
    geometries = list(fragments.geometry)
    spatial_index = fragments.sindex
    rows: list[tuple[int, int, float, float]] = []
    for left_index, left_geometry in enumerate(geometries):
        candidates = spatial_index.query(
            left_geometry.buffer(distance_m),
            predicate="intersects",
        )
        for right_index in candidates:
            right_index = int(right_index)
            if right_index <= left_index:
                continue
            right_geometry = geometries[right_index]
            distance = float(left_geometry.distance(right_geometry))
            if distance > distance_m:
                continue
            shared_length = 0.0
            if distance <= 0.0:
                try:
                    shared_length = float(left_geometry.intersection(right_geometry).length)
                except GEOSException:
                    # A source polygon can be invalid; the edge and distance are still usable.
                    shared_length = 0.0
            left_key, right_key = int(keys[left_index]), int(keys[right_index])
            if left_key > right_key:
                left_key, right_key = right_key, left_key
            rows.append(
                (
                    left_key,
                    right_key,
                    round(distance, 1),
                    round(shared_length, 1),
                )
            )
    topology = pd.DataFrame(
        rows,
        columns=["BLOCK1", "BLOCK2", "DISTANCE", "LENGTH"],
    ).drop_duplicates(["BLOCK1", "BLOCK2"])
    topology = topology.sort_values(["BLOCK1", "BLOCK2"], kind="stable")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    topology.to_csv(output_path, index=False)
    return topology


def main() -> None:
    """Build the topology from the configured block layer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--distance-m", type=float, default=0.0)
    args = parser.parse_args()
    topology = build_topology(
        fragments_path=args.fragments,
        output_path=args.out,
        distance_m=args.distance_m,
    )
    print(
        json.dumps(
            {
                "out": str(args.out),
                "edges": len(topology),
                "distance_m": args.distance_m,
                "bytes": args.out.stat().st_size,
            }
        )
    )


if __name__ == "__main__":
    main()
