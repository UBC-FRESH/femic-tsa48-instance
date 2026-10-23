# Full TSA 48 Rebuild Runbook

This is the operator-facing rebuild procedure for the full TSA 48 instance.

## Required inputs

- `config/run_profile.tsa48_full.yaml`
- `config/rebuild.spec.yaml`
- `config/rebuild.allowlist.yaml`
- The public data root in `FEMIC_EXTERNAL_DATA_ROOT`
- A `ws4` checkout or installed package

## Build

```bash
export FEMIC_EXTERNAL_DATA_ROOT=/path/to/femic-public-data/data
python -m femic run --run-config config/run_profile.tsa48_full.yaml

MODEL_DIR=runtime/tsa48_full_calibrated \
PATCHWORKS_OUT=output/patchworks_tsa48_full_calibrated \
CALIBRATE_THLB=1 \
scripts/build_full_tsa48_model.sh
```

The build script exports the inventory, compiles and validates the ws4 matrix,
flags NICC/outside/K3Z parts, builds part datasets and schedules, simulates and
reports each part, and writes the UI geometry and land-base underlay.

## Verify

```bash
python -m ws4.cli validate --dataset runtime/tsa48_full_calibrated/matrix
python scripts/report_part_accounting.py \
  --runs runtime/tsa48_full_calibrated/runs \
  --out runtime/tsa48_full_calibrated/evidence/account_values_by_part.csv
python scripts/report_tsr_benchmark.py \
  --dataset runtime/tsa48_full_calibrated/matrix \
  --part-datasets runtime/tsa48_full_calibrated \
  --runs runtime/tsa48_full_calibrated/runs \
  --schedules runtime/tsa48_full_calibrated/schedules \
  --out runtime/tsa48_full_calibrated/evidence/tsr_benchmark.csv
```

The part accounting must reconcile `full = nicc + outside`. The benchmark
target table must show all ten AAC decades inside the target band.

## Topology and opening policy

Build the touching-block topology when preparing spatial opening constraints:

```bash
python scripts/build_topology.py \
  --fragments runtime/tsa48_full_calibrated/fragments.geojson \
  --out runtime/tsa48_full_calibrated/topology.csv \
  --distance-m 0
```

The topology is not a model input until the patch accounts and targets are
configured. The opening-size policy still needs confirmation from MKRF staff on
whether the shares are maxima or minima and on the Very High/High weights.

## Web UI

```bash
./serve_tsa48_calibrated.sh
```

The service binds `127.0.0.1:8016`. Check `/health`, the run list, the target
table, and the map before reporting the instance ready.

## Evidence to archive

- `runtime/tsa48_full_calibrated/evidence/thlb_calibration.json`
- `runtime/tsa48_full_calibrated/evidence/account_values_by_part.csv`
- `runtime/tsa48_full_calibrated/evidence/account_values_by_part_reconciliation.csv`
- `runtime/tsa48_full_calibrated/evidence/tsr_benchmark.csv`
- `runtime/tsa48_full_calibrated/evidence/optimized_decades_part_share.json`
- The run summaries for `aac_benchmark`, `nicc`, and `outside`
