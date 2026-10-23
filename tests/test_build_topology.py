"""The topology builder emits the touching-block edge contract."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from build_topology import build_topology


def _fragments(path: Path, geometries: list[object]) -> Path:
    frame = gpd.GeoDataFrame(
        {"block_id": list(range(1, len(geometries) + 1))},
        geometry=geometries,
        crs="EPSG:3005",
    )
    frame.to_file(path, driver="GeoJSON")
    return path


def test_touching_blocks_get_one_topology_edge(tmp_path: Path) -> None:
    """Two polygons that share an edge have distance zero and a shared length."""
    fragments = _fragments(tmp_path / "blocks.geojson", [box(0, 0, 10, 10), box(10, 0, 20, 10)])
    out = tmp_path / "topology.csv"
    topology = build_topology(fragments_path=fragments, output_path=out, distance_m=0.0)
    assert list(topology.columns) == ["BLOCK1", "BLOCK2", "DISTANCE", "LENGTH"]
    assert len(topology) == 1
    row = topology.iloc[0]
    assert row["BLOCK1"] == 1
    assert row["BLOCK2"] == 2
    assert row["DISTANCE"] == 0.0
    assert row["LENGTH"] > 0.0
    assert pd.read_csv(out).equals(topology)


def test_distance_threshold_controls_proximal_edges(tmp_path: Path) -> None:
    """Blocks separated by 1 m are excluded at 0 m and included at 2 m."""
    fragments = _fragments(
        tmp_path / "blocks.geojson",
        [box(0, 0, 10, 10), box(11, 0, 21, 10)],
    )
    touching = build_topology(
        fragments_path=fragments, output_path=tmp_path / "touching.csv", distance_m=0.0
    )
    assert touching.empty
    proximal = build_topology(
        fragments_path=fragments, output_path=tmp_path / "proximal.csv", distance_m=2.0
    )
    assert len(proximal) == 1
    assert proximal.iloc[0]["DISTANCE"] == 1.0


def test_topology_output_is_json_serialisable(tmp_path: Path) -> None:
    """The test fixture remains inspectable as plain GeoJSON."""
    fragments = _fragments(tmp_path / "blocks.geojson", [box(0, 0, 10, 10)])
    document = json.loads(fragments.read_text(encoding="utf-8"))
    assert document["type"] == "FeatureCollection"
