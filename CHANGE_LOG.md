# Change Log

Newest entries last. Each milestone gets a dated entry that matches the roadmap
status and the GitHub issue comments.

## 2026-10-21

- Created the full TSA 48 model lane from the shared North Island FEMIC
  inventory. The build boundary is the full TSA, with NICC and K3Z retained as
  block-level part/overlay flags.

## 2026-10-22

- Built the full 110,728-block matrix on the 0-based offset clock.
- Calibrated the per-stand THLB proportion to exactly 177,505.0 ha.
- Added ten decade AAC targets at 12,480,000-12,481,000 m3 and a seed-greedy
  benchmark that meets all ten.
- Recorded the NICC part share: 2,145,437 m3 in the first decade, 17.19% of the
  full-model harvest, ≈214,544 m3/yr.
- Added exact block geometry, the AOI land-base underlay, and the web target
  window/table fixes.

## 2026-10-23

- Split the full TSA 48 lane into the standalone public
  `UBC-FRESH/femic-tsa48-instance` repository.
- Added the sibling NICC instance link and the "related but independent"
  contract to the README, AOI docs, and reference notes.
- Added `scripts/build_topology.py` for touching-block patch constraints.
