"""The land-base helper writes the AOI polygon as a GeoJSON underlay."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

from prepare_land_base import prepare_land_base


def test_prepare_land_base_writes_one_polygon(tmp_path: Path) -> None:
    """The AOI is written as one GeoJSON polygon with a summary."""
    aoi = tmp_path / "aoi.gpkg"
    frame = gpd.GeoDataFrame(
        {"aoi_name": ["tsa48"], "area_ha": [100.0]},
        geometry=[box(0, 0, 1000, 1000)],
        crs="EPSG:3005",
    )
    frame.to_file(aoi, layer="tsa48", driver="GPKG")
    out = tmp_path / "land_base.geojson"
    summary = prepare_land_base(aoi, out)
    assert summary["features"] == 1
    assert summary["crs"] == "EPSG:3005"
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["features"][0]["geometry"]["type"] == "Polygon"
    assert document["features"][0]["properties"] == {}
