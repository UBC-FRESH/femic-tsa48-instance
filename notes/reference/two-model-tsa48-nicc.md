# Full TSA 48 and NICC-overlap models

Status: full model built and served; benchmark and NICC part share recorded. The two datasets are related but independent; see `notes/reference/related-instances.md`.

## The two models

1. **Full TSA 48 benchmark model** (`runtime/tsa48_full_calibrated/matrix`)
   - Boundary: full North Island TSA 48 (`data/source/aoi/tsa48_full.gpkg`).
   - Every block carries a `part` flag (`nicc` or `outside`) and a `k3z` flag.
   - Purpose: benchmark the ws4 wood supply against the published TSA 48 AAC and
     THLB, then split the AAC between the NICC overlap and the rest of the TSA.

2. **NICC-overlap + K3Z model** (`UBC-FRESH/femic-northisland-instance`, served on port 8014)
   - Boundary: TSA 48 intersected with the North Island - Central Coast
     Natural Resource District, plus the K3Z community forest.
   - Purpose: the student/MSFM model for NICF planning, including the proposed
     8,000 ha NICF expansion.

## Reference numbers

From the North Island TSA Timber Supply Review Data Package, July 2020,
Table 4 and section 7.1.1:

| Quantity | Value |
| --- | ---: |
| TSA boundary area | 2,426,749 ha |
| Ocean removed | 677,289 ha |
| Gross land area | 1,749,460 ha |
| Section 8 decision area | 714,726 ha |
| Current THLB | 177,505 ha |
| Current AAC | 1,248,100 m³/yr |

The NICC intersection is 1,083,003.66 ha gross. The published AAC and THLB are
for the whole TSA, which is why the full-TSA model is the benchmark and the
NICC-only model cannot use those numbers directly.

## Part accounting

The full model's `part` flag is in `blocks.parquet` and `fragments.parquet`, and
in the UI GeoJSON properties. Because ws4 reports state/area accounts over the
dataset fragments rather than the scheduled blocks, the accounting views are
separate filtered datasets:

- `runtime/tsa48_full_calibrated/matrix_nicc`
- `runtime/tsa48_full_calibrated/matrix_outside`

Each is a valid ws4 matrix with the same tracks, curves, treatments, and
products; only the fragment/block tables are filtered. Simulating the full,
NICC, and outside schedules against the matching dataset makes every account
reconcile exactly (`full = nicc + outside`).

Evidence files:

- `runtime/tsa48_full_calibrated/evidence/account_values_by_part.csv`
- `runtime/tsa48_full_calibrated/evidence/account_values_by_part_reconciliation.csv`
- `runtime/tsa48_full_calibrated/evidence/tsr_benchmark.csv`

## Build result

| Quantity | Full TSA 48 | NICC part | Outside part |
| --- | ---: | ---: | ---: |
| Blocks | 110,728 | 51,292 | 59,436 |
| Block area | 1,092,831.62 ha | 442,591.61 ha | 650,240.01 ha |
| Model managed area | 130,481.59 ha | 28,557.95 ha | 101,923.64 ha |

The K3Z flag touches 253 blocks and 2,093.48 ha.

The NICC part is almost identical to the existing 8014 model (442,451.9974 ha,
51,289 blocks), which confirms the two builds agree on the overlap.

## Baseline benchmark

The deterministic clearcut-at-age-60 baseline overharvests the full TSA
(2.83M m3/yr on average, 227% of the 1,248,100 m3/yr AAC). The model managed
area is 130,481.59 ha, or 73.5% of the published 177,505 ha THLB. The NICC part
is 28,557.95 ha, or 16.1% of the published THLB.

The first optimization run held the first-decade harvest to 9,977,924 m3
(80.0% of the 12,481,000 m3 first-decade AAC). The model cannot reach the
published AAC without reconciling the land base/yields with the TSR netdown.
For the uncalibrated proportional variant, the optimized NICC first-decade
share is 10.31% of the full model harvest, which scales to a provisional
reference of about **128,657 m3/yr** of the legal AAC. The calibrated variant
is the primary reference; see the calibrated optimized share below.

## Calibrated THLB variant

The default proportional export gives 130,481.59 ha of managed area. To
calibrate the per-stand THLB proportion to the published 177,505 ha reference,
`scripts/calibrate_thlb_proportion.py` scales `thlb_raw / 100` by
**1.4461532388060396**, caps it at `1.0`, and writes
`thlb_raw_calibrated`. The capped area is exactly **177,505.0 ha**; 6,018
stands saturate to fully managed.

The calibrated model is built under `runtime/tsa48_full_calibrated/`:

| Quantity | Calibrated full TSA 48 | NICC part | Outside part |
| --- | ---: | ---: | ---: |
| Blocks | 110,728 | 51,292 | 59,436 |
| Block area | 1,092,831.62 ha | 442,591.61 ha | 650,240.01 ha |
| Model managed area | 177,505.00 ha | 38,960.29 ha | 138,544.71 ha |
| Share of TSR THLB | 100.0% | 21.95% | 78.05% |

The calibration is a reviewed area calibration, not a replacement for the
reviewed TSR netdown sequence. The part accounting reconciles exactly
(`full = nicc + outside`, max error 1.1e-5).

### Calibrated optimized share

The corrected offset-clock benchmark uses ten per-decade AAC targets with a
12,480,000-12,481,000 m3 band (the 1,248,100 m3/yr AAC, with a 0.008% rounding
tolerance). The seed-greedy schedule holds every decade inside that band, with
9,335 blocks and 17,574 treatment events (some blocks carry a second rotation).

The NICC part contributes:

- first-decade harvest: **2,145,437 m3**
- NICC share of the full-model first-decade harvest: **17.19%**
- NICC share of the full-model total harvest: 16.72%
- scaled to the legal AAC: **≈214,544 m3/yr**
- NICC's own first-decade annual average: 214,544 m3/yr

That is the current reference for the NICC model. The earlier 9.97M m3 / 80%
result was an artifact of the old schedule `period`/year off-by-one and is
superseded.

## Reproduction

```bash
export FEMIC_EXTERNAL_DATA_ROOT=/path/to/femic-public-data/data
python -m femic run --run-config config/run_profile.tsa48_full.yaml
scripts/build_full_tsa48_model.sh
./serve_tsa48_calibrated.sh   # port 8016
```
