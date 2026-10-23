"""Tests for the ws4 web UI geometry preparation script."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from prepare_ws4_ui import _round_coordinates, main, prepare_ui_geometry


def test_prepare_ui_geometry_dissolves_fragments_to_blocks(tmp_path: Path) -> None:
    """Two fragments of one block become one UI feature with a block_id."""
    source = tmp_path / "fragments.geojson"
    gpd.GeoDataFrame(
        {
            "BLOCK": [7, 7, 8],
            "FRAGMENT_ID": [1, 2, 3],
            "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(3, 0, 4, 1)],
        },
        crs="EPSG:3005",
    ).to_file(source, driver="GeoJSON")
    out = tmp_path / "ui.geojson"

    summary = prepare_ui_geometry(fragments=source, out=out)

    result = gpd.read_file(out)
    assert summary["block_count"] == 2
    assert sorted(result["block_id"].tolist()) == [7, 8]
    assert result.crs is not None


def test_prepare_ui_geometry_rejects_unknown_block_column(tmp_path: Path) -> None:
    """Fragment geometry without a block key is rejected."""
    source = tmp_path / "fragments.geojson"
    gpd.GeoDataFrame(
        {"FRAGMENT_ID": [1], "geometry": [box(0, 0, 1, 1)]},
        crs="EPSG:3005",
    ).to_file(source, driver="GeoJSON")

    with pytest.raises(ValueError, match="BLOCK"):
        prepare_ui_geometry(fragments=source, out=tmp_path / "ui.geojson")


def test_round_coordinates_recurses_and_preserves_non_floats() -> None:
    """Nested coordinates are rounded; integer and string values pass through."""
    value = _round_coordinates([1.23456, [2.34567, "x"], 3], 2)
    assert value == [1.23, [2.35, "x"], 3]


def test_prepare_ui_geometry_can_skip_simplification(tmp_path: Path) -> None:
    """A zero tolerance preserves the original polygon vertices."""
    source = tmp_path / "fragments.geojson"
    gpd.GeoDataFrame(
        {"BLOCK": [1], "geometry": [box(0, 0, 10, 10)]},
        crs="EPSG:3005",
    ).to_file(source, driver="GeoJSON")
    out = tmp_path / "ui.geojson"

    summary = prepare_ui_geometry(fragments=source, out=out, simplify_m=0.0)

    assert summary["simplify_m"] == 0.0
    assert out.is_file()


def test_main_writes_the_ui_geometry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI entry point writes the requested output."""
    source = tmp_path / "fragments.geojson"
    gpd.GeoDataFrame(
        {"BLOCK": [1], "geometry": [box(0, 0, 10, 10)]},
        crs="EPSG:3005",
    ).to_file(source, driver="GeoJSON")
    out = tmp_path / "ui.geojson"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare_ws4_ui.py",
            "--fragments",
            str(source),
            "--out",
            str(out),
        ],
    )

    main()

    assert out.is_file()
