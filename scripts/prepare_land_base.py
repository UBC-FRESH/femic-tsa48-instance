#!/usr/bin/env python
"""Write the AOI polygon as the web map's non-forest underlay.

The block layer covers forest only. Drawing the gross AOI beneath it keeps the gaps in the
inventory (non-forest, water, roads) from reading as missing map data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd


def prepare_land_base(aoi: Path, out: Path) -> dict[str, object]:
    """Write the AOI polygon as a GeoJSON underlay and return its summary.

    Parameters
    ----------
    aoi : Path
        AOI polygon in a GeoPackage or shapefile.
    out : Path
        Destination GeoJSON.

    Returns
    -------
    dict of str to object
        Output path, feature count, CRS and byte size.
    """
    frame = gpd.read_file(aoi)
    if frame.empty:
        raise SystemExit(f"{aoi} has no features")
    frame = frame[["geometry"]].copy()
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_file(out, driver="GeoJSON")
    document = json.loads(out.read_text(encoding="utf-8"))
    return {
        "out": str(out),
        "features": len(document.get("features", [])),
        "crs": str(frame.crs),
        "bytes": out.stat().st_size,
    }


def main() -> None:
    """Write the AOI land-base GeoJSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aoi", type=Path, required=True, help="AOI polygon (GPKG or SHP)")
    parser.add_argument("--out", type=Path, required=True, help="Output GeoJSON")
    args = parser.parse_args()
    print(json.dumps(prepare_land_base(args.aoi, args.out)))


if __name__ == "__main__":
    main()
