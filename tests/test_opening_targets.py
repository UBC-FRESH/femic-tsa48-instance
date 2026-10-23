"""The opening-policy targets cover every class and accounting period."""

from __future__ import annotations

from pathlib import Path

import yaml

from build_opening_targets import PATCH_CLASSES, combine_targets, opening_targets


def test_opening_targets_cover_each_class_and_period() -> None:
    """Ten periods times four constrained classes gives forty targets."""
    rows = opening_targets(periods=10, period_width=10)
    assert len(rows) == 40
    assert {row["account"] for row in rows} == {row[0] for row in PATCH_CLASSES}
    assert {row["period"] for row in rows} == set(range(1, 11))
    assert all(row["period_width"] == 10 for row in rows)


def test_opening_targets_are_maxima() -> None:
    """The current implementation treats the shares as maxima."""
    rows = opening_targets()
    assert all("maximum" in row and "minimum" not in row for row in rows)
    assert all(bool(row["max_weight"]) for row in rows)


def test_combine_targets_preserves_the_aac_targets(tmp_path: Path) -> None:
    """The generated file keeps the base AAC rows before the patch rows."""
    base = tmp_path / "base.yaml"
    base.write_text(
        yaml.safe_dump(
            {
                "targets": [
                    {
                        "account": "product.Yield.managed.Total",
                        "period": 1,
                        "period_width": 10,
                        "minimum": 12480000,
                        "maximum": 12481000,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    rows = combine_targets(base, periods=2, period_width=10)
    assert rows[0]["account"] == "product.Yield.managed.Total"
    assert len(rows) == 9
    assert rows[-1]["account"] == "patch.grpblk.50_9999999.size"
