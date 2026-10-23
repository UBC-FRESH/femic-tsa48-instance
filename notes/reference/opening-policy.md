# Opening-size policy and the opening-first AAC schedule

Status: opening policy applied to the full TSA 48 benchmark; one AAC decade is 39 m3 below the
strict lower bound.

## Policy

The MKRF staff guidance is expressed as opening-size **ceilings** (confirmed
October 2026). The Very High/High numeric weights are an implementation
calibration, not a policy statement.

| Class | Maximum share | Weight |
| --- | ---: | ---: |
| `<= 1 ha` | 0% | Very High, 10,000,000 |
| `> 1-5 ha` | 10% | High, 1,000,000 |
| `> 5-40 ha` | none | none |
| `> 40-50 ha` | 5% | High, 1,000,000 |
| `> 50 ha` | 0% | High, 1,000,000 |

The patch account joins only blocks that touch (`search_distance: 0.0`) and
uses `product.Treated.managed.CC` as the treated-area criterion:
`config/patch_accounts.tsa48_full.yaml`.

## Topology

The full TSA topology is built from the exact block geometry:

```bash
python scripts/build_topology.py \
  --fragments runtime/tsa48_full_calibrated/fragments.geojson \
  --out runtime/tsa48_full_calibrated/topology.csv \
  --distance-m 0
```

It has **234,547 touching edges** over the 110,728 blocks.

## The volume-only benchmark does not satisfy the policy

The existing `aac_benchmark` schedule meets the ten AAC targets but produces
large same-year openings. At the ten decade-end snapshots, every decade has
some 1-5 ha share above the 10% maximum or a 40-50/>50 ha share.

## Opening-first schedule

`scripts/build_opening_schedule.py` builds connected 5-40 ha openings first,
then assigns offsets within each decade. A final adjacency check prevents two
touching openings from receiving the same offset, which is what caused merged
openings above 40 ha in the first pass.

Command:

```bash
python scripts/build_opening_schedule.py \
  --dataset runtime/tsa48_full_calibrated/matrix \
  --topology runtime/tsa48_full_calibrated/topology.csv \
  --out runtime/tsa48_full_calibrated/schedules/opening_first.csv \
  --years 100 --min-area 5 --max-area 40 \
  --target-per-decade 12481000 --intermediate-share 0
```

Result:

- 10,351 openings; 16,933 scheduled blocks; 136,914.0 ha of opening area.
- Opening range: 5.0-40.0 ha.
- At **every year** in the 100-year simulation, 100% of patch area is in the
  5-40 ha class; the 0-1, 1-5, 40-50 and >50 classes are all 0.0%.
- 100-year managed volume: 124,807,746.86 m3; average 1,248,077.47 m3/yr.

AAC by decade:

| Decade | Volume (m3) | Strict 12,480,000-12,481,000 band |
| --- | ---: | --- |
| 1 | 12,480,948.83 | inside |
| 2 | 12,480,988.28 | inside |
| 3 | 12,480,587.56 | inside |
| 4 | 12,480,989.62 | inside |
| 5 | 12,480,869.88 | inside |
| 6 | 12,480,717.46 | inside |
| 7 | 12,479,961.11 | 38.89 m3 below |
| 8 | 12,480,935.12 | inside |
| 9 | 12,480,887.47 | inside |
| 10 | 12,480,861.54 | inside |

The decade-7 shortfall is 0.00031% of the decade target, within the benchmark's
stated rounding scale, but a literal target report will mark it below. The
schedule is a deterministic opening-first seed, not an optimized final plan.

## Interpretation

The policy is spatially feasible at full-TSA scale: the schedule can form
5-40 ha openings across the whole horizon while carrying effectively the full
AAC. The remaining work is to decide whether the 39 m3 tolerance is acceptable
or to add a small fill/optimization step, and to confirm the policy weights
with MKRF staff.
