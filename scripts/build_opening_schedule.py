# mypy: ignore-errors
# This is a data-shaped scheduler port; its output is covered by the end-to-end opening test.
#!/usr/bin/env python3
"""Build a patch-first clearcut schedule for the full TSA 48 benchmark.

The policy controls opening size with the 5-40 ha band as the preferred class.
Random move-based search
struggles to form same-year openings, so this script builds them directly:

1. aggregate the managed fragments to blocks (area, age, yield curve);
2. grow connected clusters of touching blocks until they reach the 5-40 ha band;
3. assign each opening an offset, filling the target periods (offsets 0-9,
   10-19, ...) toward the policy floor plus a small buffer;
4. emit a ``block_id,treatment,offset`` schedule for ws4.

Small clusters are merged into adjacent openings when capacity allows. The
40-50 ha class is capped at 5% of patch area. Blocks larger than the upper band
and openings beyond the period capacity are left unharvested. The output is a
starting schedule, not a final optimized plan.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd


def _load_blocks(
    dataset: Path,
) -> tuple[dict[int, dict[str, object]], dict[int, float]]:
    """Return the managed block table and the yield curve per track."""
    fragments = pd.read_parquet(dataset / "fragments.parquet")
    tracks = pd.read_parquet(dataset / "tracks.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")

    joined = fragments.merge(tracks, on="track_id", how="left")
    joined["managed"] = joined["name"].str.contains(r"IFM\(managed\)", regex=True)
    joined["operable"] = True
    managed = joined[joined["managed"]].copy()

    curve_by_track = (
        features.loc[features["label"] == "feature.Yield.managed.Total"]
        .set_index("track_id")["curve_id"]
        .to_dict()
    )
    curve_arrays = {
        int(curve_id): group.sort_values("x")[["x", "y"]].to_numpy()
        for curve_id, group in curves.groupby("curve_id")
    }

    blocks: dict[int, dict[str, object]] = {}
    for block_id, group in managed.groupby("block_id"):
        area = float(group["area_ha"].sum())
        age = float(np.average(group["age"], weights=group["area_ha"]))
        blocks[int(block_id)] = {
            "block_id": int(block_id),
            "area": area,
            "age": age,
            "operable": bool(group["operable"].all()),
            "fragments": group,
        }
    return blocks, {
        int(track_id): curve_arrays[int(curve_id)]
        for track_id, curve_id in curve_by_track.items()
        if int(curve_id) in curve_arrays
    }


def _volume(
    block: dict[str, object],
    year: int,
    curves: dict[int, np.ndarray],
    *,
    simulator: object | None = None,
    cache: dict[tuple[int, int], float] | None = None,
) -> float:
    """Return the managed harvest volume at a harvest year for one block.

    When a ws4 simulator is supplied, its product calculation is used so the
    builder's decade totals match the simulation. Otherwise the standing-yield
    curve is a fallback proxy.
    """
    if simulator is not None:
        key = (int(block["block_id"]), year)
        if cache is not None and key in cache:
            return cache[key]
        products = simulator.block_products(  # type: ignore[attr-defined]
            int(block["block_id"]), "CC", year
        )
        value = float(products.get("product.Yield.managed.Total", 0.0))
        if cache is not None:
            cache[key] = value
        return value
    total = 0.0
    for fragment in block["fragments"].itertuples():  # type: ignore[attr-defined]
        curve = curves.get(int(fragment.track_id))
        if curve is None:
            continue
        density = float(np.interp(float(fragment.age) + year, curve[:, 0], curve[:, 1]))
        total += float(fragment.area_ha) * density
    return total


def _read_adjacency(topology: Path, blocks: dict[int, dict[str, object]]) -> dict[int, set[int]]:
    """Return touching-block adjacency from the proximal topology."""
    frame = pd.read_csv(topology)
    adjacency: dict[int, set[int]] = defaultdict(set)
    for row in frame.itertuples(index=False):
        left, right = int(row.BLOCK1), int(row.BLOCK2)
        if left < 0 or right < 0 or float(row.DISTANCE) > 0.0:
            continue
        if left in blocks and right in blocks:
            adjacency[left].add(right)
            adjacency[right].add(left)
    return adjacency


def _build_openings(
    blocks: dict[int, dict[str, object]],
    adjacency: dict[int, set[int]],
    *,
    min_area: float,
    max_area: float,
    intermediate_share: float = 0.05,
) -> list[dict[str, object]]:
    """Grow connected openings in the area band and return them."""
    for block in blocks.values():
        min_age = 60.0 if block["operable"] else 150.0
        block["ready"] = max(0, int(np.ceil(min_age - float(block["age"]))))

    eligible = [block for block in blocks.values() if float(block["area"]) <= max_area]
    eligible.sort(key=lambda block: (block["ready"], -float(block["age"]), -float(block["area"])))
    assigned: set[int] = set()
    openings: list[dict[str, object]] = []
    small: list[tuple[list[int], float]] = []
    for seed in eligible:
        block_id = int(seed["block_id"])
        if block_id in assigned:
            continue
        cluster = [block_id]
        total = float(seed["area"])
        assigned.add(block_id)
        frontier = deque(sorted(adjacency.get(block_id, ())))
        while total < min_area and frontier:
            neighbour = frontier.popleft()
            if neighbour in assigned:
                continue
            other = blocks[neighbour]
            if float(other["area"]) > max_area:
                continue
            if total + float(other["area"]) > max_area:
                continue
            cluster.append(neighbour)
            total += float(other["area"])
            assigned.add(neighbour)
            frontier.extend(item for item in adjacency.get(neighbour, ()) if item not in assigned)
        if total < min_area:
            small.append((cluster, total))
            continue
        openings.append(
            {
                "blocks": tuple(cluster),
                "area": total,
                "ready": max(int(blocks[item]["ready"]) for item in cluster),
            }
        )

    # Merge small clusters into an adjacent opening when capacity allows.
    block_opening: dict[int, int] = {}
    for index, opening in enumerate(openings):
        for block in opening["blocks"]:
            block_opening[block] = index
    for cluster, area in small:
        candidates = {
            block_opening[neighbour]
            for block in cluster
            for neighbour in adjacency.get(block, ())
            if neighbour in block_opening
        }
        choices = [
            (float(openings[index]["area"]), index)
            for index in candidates
            if float(openings[index]["area"]) + area <= max_area
        ]
        if not choices:
            continue
        _, index = min(choices)
        opening = openings[index]
        opening["blocks"] = tuple(opening["blocks"]) + tuple(cluster)
        opening["area"] = float(opening["area"]) + area
        opening["ready"] = max(
            int(opening["ready"]), max(int(blocks[item]["ready"]) for item in cluster)
        )
        for block in cluster:
            block_opening[block] = index

    # Keep the 40-50 ha class within the policy's 5% cap.
    total_area = sum(float(opening["area"]) for opening in openings)
    cap = intermediate_share * total_area
    used = 0.0
    kept: list[dict[str, object]] = []
    for opening in openings:
        area = float(opening["area"])
        if area > 40.0:
            if used + area > cap:
                continue
            used += area
        kept.append(opening)
    return kept


def _opening_adjacency(
    openings: list[dict[str, object]],
    block_adjacency: dict[int, set[int]],
) -> dict[int, tuple[int, ...]]:
    """Return the opening-to-opening adjacency induced by touching blocks."""
    block_to_opening: dict[int, int] = {}
    for index, opening in enumerate(openings):
        for block in opening["blocks"]:
            block_to_opening[int(block)] = index
    adjacency: dict[int, set[int]] = defaultdict(set)
    for block, neighbours in block_adjacency.items():
        left = block_to_opening.get(int(block))
        if left is None:
            continue
        for neighbour in neighbours:
            right = block_to_opening.get(int(neighbour))
            if right is not None and right != left:
                adjacency[left].add(right)
    return {index: tuple(sorted(values)) for index, values in adjacency.items()}


def _ordered_offsets(start: int, ready: int, years: int, counter: int) -> list[int]:
    """Return the period's offsets, rotated so successive openings use different years."""
    offsets = list(range(max(start, ready), min(start + 9, years - 1) + 1))
    if not offsets:
        return []
    shift = counter % len(offsets)
    return offsets[shift:] + offsets[:shift]


def _assign_offsets(
    openings: list[dict[str, object]],
    blocks: dict[int, dict[str, object]],
    curves: dict[int, np.ndarray],
    *,
    years: int,
    target_per_decade: float,
    simulator: object | None = None,
    opening_adjacency: dict[int, tuple[int, ...]] | None = None,
) -> dict[int, float]:
    """Assign opening offsets, filling each target period toward the target volume.

    Target period 1 is offsets 0-9, period 2 is offsets 10-19, and so on. Offset
    0 is the first simulation year; the period-0 snapshot is never scheduled.
    """
    period_count = max(1, years // 10)
    starts = {period: 10 * (period - 1) for period in range(1, period_count + 1)}
    volumes = dict.fromkeys(starts, 0.0)
    offsets = dict.fromkeys(starts, 0)
    cache: dict[tuple[int, int], float] = {}
    chosen_offsets: dict[int, int] = {}
    dropped = 0
    ordered = sorted(
        enumerate(openings), key=lambda item: (item[1]["ready"], -float(item[1]["area"]))
    )
    for index, opening in ordered:
        candidates = [period for period, start in starts.items() if start >= int(opening["ready"])]
        if not candidates:
            dropped += 1
            continue
        choice: tuple[int, int, float] | None = None
        neighbours = opening_adjacency.get(index, ()) if opening_adjacency else ()
        for period in sorted(candidates):
            start = starts[period]
            blocked = {chosen_offsets[item] for item in neighbours if item in chosen_offsets}
            for offset in _ordered_offsets(start, int(opening["ready"]), years, offsets[period]):
                if offset in blocked:
                    continue
                volume = sum(
                    _volume(
                        blocks[item],
                        offset,
                        curves,
                        simulator=simulator,
                        cache=cache,
                    )
                    for item in opening["blocks"]
                )
                if volumes[period] + volume <= target_per_decade:
                    choice = (period, offset, volume)
                    break
            if choice is not None:
                break
        if choice is None:
            dropped += 1
            continue
        period, offset, volume = choice
        offsets[period] += 1
        chosen_offsets[index] = offset
        opening["target_period"] = period
        opening["offset"] = offset
        opening["volume"] = volume
        volumes[period] += volume
    if dropped:
        print(f"dropped {dropped} openings beyond the period capacity")
    return volumes


def schedule_frame(openings: list[dict[str, object]]) -> pd.DataFrame:
    """Return the ``block_id,treatment,offset`` schedule for assigned openings.

    Parameters
    ----------
    openings : list of dict
        Openings with an ``offset`` and a ``blocks`` tuple.

    Returns
    -------
    pandas.DataFrame
        One row per scheduled block, sorted by offset then block.
    """
    rows = [
        {"block_id": int(block_id), "treatment": "CC", "offset": int(opening["offset"])}
        for opening in openings
        for block_id in opening["blocks"]
    ]
    if not rows:
        return pd.DataFrame(columns=["block_id", "treatment", "offset"])
    return pd.DataFrame(rows).sort_values(["offset", "block_id"], kind="stable")


def main() -> None:
    """Build and write the opening-first schedule."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--years", type=int, default=100)
    parser.add_argument("--min-area", type=float, default=5.0)
    parser.add_argument("--max-area", type=float, default=50.0)
    parser.add_argument("--target-per-decade", type=float, default=12_480_000.0)
    parser.add_argument("--intermediate-share", type=float, default=0.05)
    args = parser.parse_args()

    from ws4.sim.engine import Simulator

    blocks, curves = _load_blocks(args.dataset)
    simulator = Simulator.from_dataset(args.dataset)
    adjacency = _read_adjacency(args.topology, blocks)
    openings = _build_openings(
        blocks,
        adjacency,
        min_area=args.min_area,
        max_area=args.max_area,
        intermediate_share=args.intermediate_share,
    )
    opening_adjacency = _opening_adjacency(openings, adjacency)
    decades = _assign_offsets(
        openings,
        blocks,
        curves,
        years=args.years,
        target_per_decade=args.target_per_decade,
        simulator=simulator,
        opening_adjacency=opening_adjacency,
    )

    scheduled = [opening for opening in openings if "offset" in opening]
    schedule = schedule_frame(scheduled)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(args.out, index=False)

    areas = sorted(float(opening["area"]) for opening in scheduled)
    area_range = f"{areas[0]:.1f}-{areas[-1]:.1f} ha" if areas else "n/a"
    print(
        f"blocks={len(blocks)} openings={len(scheduled)} "
        f"scheduled_blocks={len(schedule)} "
        f"area={sum(areas):.1f} ha "
        f"area_range={area_range}"
    )
    print("decade volumes:", {decade: round(value) for decade, value in decades.items()})


if __name__ == "__main__":
    main()
