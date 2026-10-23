# Full TSA 48 ws4 build evidence

The calibrated full model is built by `scripts/build_full_tsa48_model.sh` from
the FEMIC export. The Patchworks XML/fragments pair is an interchange input to
`ws4 build`; Patchworks is not the runtime lane.

## Command

```bash
MODEL_DIR=runtime/tsa48_full_calibrated \
PATCHWORKS_OUT=output/patchworks_tsa48_full_calibrated \
CALIBRATE_THLB=1 \
scripts/build_full_tsa48_model.sh
```

The script exports the inventory, compiles and validates the ws4 matrix, flags
NICC/outside/K3Z parts, builds part datasets and schedules, simulates and
reports each part, and writes the exact UI geometry and land-base underlay.

## Dataset

| Table | Full TSA 48 |
| --- | ---: |
| Blocks | 110,728 |
| Block area | 1,092,831.62 ha |
| Managed area (calibrated) | 177,505.00 ha |
| NICC part | 51,292 blocks / 38,960.29 managed ha |
| Outside part | 59,436 blocks / 138,544.71 managed ha |

The calibrated THLB scales `thlb_raw / 100` by
`1.4461532388060396`, capped at `1.0`. The cap yields exactly 177,505.0 ha;
6,018 stands saturate.

## Validation

- `ws4 build` and `ws4 validate` pass for the full and part matrices.
- Part accounting reconciles: `full = nicc + outside`.
- `config/targets.tsa48_full.yaml` is the ten-decade AAC target set.
- `runtime/tsa48_full_calibrated/evidence/` holds the calibration, part
  accounting and TSR benchmark reports.

## Related dataset

The NICC + K3Z model is built independently in
`UBC-FRESH/femic-northisland-instance`. It can use this model's NICC share as a
reference, but neither build requires the other.
