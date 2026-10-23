"""Helpers in the opening-first schedule builder keep touching openings apart."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_opening_schedule.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_opening_schedule", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_opening_adjacency_follows_touching_blocks() -> None:
    """Two openings that share a topology edge are adjacent."""
    module = _load_module()
    openings = [{"blocks": (1, 2)}, {"blocks": (3,)}]
    adjacency = {1: {2}, 2: {1, 3}, 3: {2}}
    result = module._opening_adjacency(openings, adjacency)
    assert 0 in result
    assert 1 in result
    assert set(result[0]) == {1}
    assert set(result[1]) == {0}


def test_ordered_offsets_rotate_within_the_decade() -> None:
    """The offset order rotates, so consecutive openings do not all share one year."""
    module = _load_module()
    assert module._ordered_offsets(10, 10, 100, 0) == list(range(10, 20))
    assert module._ordered_offsets(10, 10, 100, 2) == [*range(12, 20), 10, 11]


def test_schedule_frame_has_the_offset_schema() -> None:
    """The builder output is block_id,treatment,offset and never period."""
    module = _load_module()
    frame = module.schedule_frame([{"blocks": (1, 2), "offset": 7}])
    assert list(frame.columns) == ["block_id", "treatment", "offset"]
    assert set(frame["offset"]) == {7}
    assert set(frame["treatment"]) == {"CC"}
