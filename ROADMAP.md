# FEMIC TSA 48 Instance Roadmap

This roadmap is the plan of record for the full North Island TSA 48 benchmark
instance. Keep it in step with `CHANGE_LOG.md`, `notes/`, and the GitHub issues.
`scripts/check_workflow.py` parses the phase headers, status lines, and
checkboxes below.

Every new phase starts as `planned` with a parent issue. Activate it only
after its parent issue exists and the maintainer approves it.

## Issue Tracker Map

| Phase | Parent issue | Branch | Status |
| --- | --- | --- | --- |
| P0 Bootstrap | #1 | `main` | complete |
| P1 Full TSA AOI and public data | #2 | `feature/tsa48-aoi` | complete |
| P2 FEMIC upstream build | #3 | `feature/tsa48-upstream` | complete |
| P3 Full model and part accounting | #4 | `feature/tsa48-model` | complete |
| P4 Calibrated THLB and AAC benchmark | #5 | `feature/tsa48-benchmark` | complete |
| P5 UI, topology and related-instance docs | #6 | `feature/tsa48-ui` | complete |
| P6 Release and clean-checkout verification | #7 | `feature/tsa48-release` | planned |

## Phase 0: Bootstrap

Parent issue: #1
Branch: `main`
Status: complete

Goal: establish the public instance repository and the reproducible build
surface.

- [x] P0.1 Create the public `femic-tsa48-instance` repository
- [x] P0.2 Carry the FEMIC and ws4 instance scaffold
- [x] P0.3 Record the public-data and private-overlay boundary
- [x] P0.4 Add the green dashboard and CI workflow

Acceptance criteria:

- `python scripts/dashboard.py` is green.
- No generated runtime, private financial data, or machine-specific paths are tracked.

## Phase 1: Full TSA AOI and public data

Parent issue: #2
Branch: `feature/tsa48-aoi`
Status: complete

Goal: use the full TSA 48 gross boundary and retain the NICC/K3Z overlays for
part accounting.

- [x] P1.1 Track the full TSA 48 boundary
- [x] P1.2 Track the NICC district/intersection and K3Z overlays
- [x] P1.3 Record the public-data manifest
- [x] P1.4 Cross-reference the independent NICC instance

Acceptance criteria:

- The build boundary is `data/source/aoi/tsa48_full.gpkg`.
- NICC and K3Z are flags, not separate build boundaries in this repository.
- The related-instance note names both repositories and their independent scopes.

## Phase 2: FEMIC upstream build

Parent issue: #3
Branch: `feature/tsa48-upstream`
Status: complete

Goal: compile the public inventory and yield curves for the full TSA.

- [x] P2.1 Run the VDYP curve build
- [x] P2.2 Assemble the model-input bundle
- [x] P2.3 Export the ForestModel XML and fragments for ws4
- [x] P2.4 Record the provisional managed-curve boundary

Acceptance criteria:

- The export has 110,728 fragments and the expected curve count.
- The run manifest and diagnostics are recorded.
- The managed curve lane is explicitly provisional until accepted TIPSY output lands.

## Phase 3: Full model and part accounting

Parent issue: #4
Branch: `feature/tsa48-model`
Status: complete

Goal: compile and validate the full ws4 matrix, then split the NICC and outside
accounting.

- [x] P3.1 Build and validate the full matrix
- [x] P3.2 Flag `part = nicc` / `outside` and `k3z`
- [x] P3.3 Build the filtered part datasets
- [x] P3.4 Reconcile `full = nicc + outside`

Acceptance criteria:

- Full model: 110,728 blocks and 1,092,831.62 ha of block area.
- NICC: 51,292 blocks / 442,591.61 ha; outside: 59,436 / 650,240.01 ha.
- Part accounting reconciles within numerical tolerance.

## Phase 4: Calibrated THLB and AAC benchmark

Parent issue: #5
Branch: `feature/tsa48-benchmark`
Status: complete

Goal: calibrate the managed area to the published TSR THLB and run the
ten-decade AAC benchmark.

- [x] P4.1 Calibrate the per-stand THLB proportion
- [x] P4.2 Write the ten-decade AAC target band
- [x] P4.3 Build the seed-greedy benchmark schedule
- [x] P4.4 Record the NICC share reference

Acceptance criteria:

- Calibrated managed area is exactly 177,505.0 ha.
- All ten decade targets are met at 12,480,000-12,481,000 m3.
- The NICC share is recorded as ≈214,544 m3/yr.

## Phase 5: UI, topology and related-instance docs

Parent issue: #6
Branch: `feature/tsa48-ui`
Status: complete

Goal: finish the full-model UI and the deliberately related, independent
instance documentation.

- [x] P5.1 Serve exact block geometry and the land-base underlay
- [x] P5.2 Add the block topology builder for spatial constraints
- [x] P5.3 Add the opening-size patch accounts and targets (#8)
- [x] P5.4 Reconcile the AAC benchmark with the opening policy (#9)
- [x] P5.5 Record the related-instance cross-references in both repositories

Acceptance criteria:

- The full-model UI renders 110,728 blocks and the target table.
- Opening size classes and policy targets are explicit in `config/`.
- The AAC schedule is evaluated against the opening policy and the result is recorded.
- The TSA 48 and NICC repositories link to each other without implying a required dependency.

## Phase 6: Release and clean-checkout verification

Parent issue: #7
Branch: `feature/tsa48-release`
Status: planned

Goal: verify the repository from a clean checkout and publish the reviewed
instance artifacts.

- [ ] P6.1 Rebuild the matrix and benchmark from a clean checkout
- [ ] P6.2 Record the release notes and known gaps
- [ ] P6.3 Tag and publish after approval

Acceptance criteria:

- A clean checkout reproduces the matrix and AAC benchmark.
- The release names the exact commit, data root, and runtime versions.
- No private data or generated model output is tracked.

## Detailed Next Steps Notes

1. The full model is the benchmark scale; the NICC model is the district scale.
2. The two instances share public inputs but not compiled matrices or runs.
3. Add new shared assumptions to both `notes/reference/related-instances.md` files.
4. Keep the NICC share reference current when the full benchmark changes.
