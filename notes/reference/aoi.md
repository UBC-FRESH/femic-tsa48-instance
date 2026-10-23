# TSA 48 AOI and overlays

Status: full TSA 48 boundary accepted for the benchmark model.

## Decision

The benchmark model uses the **full North Island TSA 48** boundary, not the
NICC district clip. The published AAC (1,248,100 m3/yr) and THLB (177,505 ha)
are TSA-wide, so the full TSA is the only defensible scale for the AAC
benchmark.

The NICC district and K3Z tenure are retained as block-level overlays:

| Layer | Source | Use |
| --- | --- | --- |
| TSA 48 | `data/source/aoi/tsa48_full.gpkg` | model boundary |
| NICC district | `data/source/aoi/nicc_district.gpkg` | `part = nicc` |
| NICC intersection | `data/source/aoi/tsa48_nicc.gpkg` | reviewed overlap |
| K3Z tenure | `data/source/aoi/k3z_tenure.gpkg` | `k3z` flag |

## Reviewed numbers

| Quantity | Value |
| --- | ---: |
| TSA 48 gross area | 2,441,931.03 ha |
| TSA 48 ∩ NICC gross area | 1,083,012.84 ha |
| K3Z blocks | 253 |
| K3Z block area | 2,093.48 ha |

The full model has 110,728 blocks and 1,092,831.62 ha of block area; NICC is
51,292 blocks / 442,591.61 ha and outside is 59,436 blocks / 650,240.01 ha.

## Related dataset

The NICC + K3Z model is a separate, independent instance:
`UBC-FRESH/femic-northisland-instance`. The two can be used together or
separately. The full model's `part` flag is the accounting bridge. See
`notes/reference/related-instances.md`.
