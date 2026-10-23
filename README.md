# FEMIC Full TSA 48 Instance

Public FEMIC and ws4 model instance for the full North Island TSA 48 AOI.
FEMIC rebuilds the inventory and yield curves from public BC data; ws4 compiles
the model, runs the benchmark, and serves the web UI.

## Runtime lane

**ws4 is the primary runtime.** The Patchworks XML/fragments package is an
interchange input to `ws4 build`, not the runtime lane. The retained Patchworks
model packages are reference evidence for comparison and rebuild provenance.

## Related instance

This repository is deliberately related to
**[`UBC-FRESH/femic-northisland-instance`](https://github.com/UBC-FRESH/femic-northisland-instance)**,
the TSA 48 ∩ NICC + K3Z model. They share the same public inventory and FEMIC
export lane, but they are **independent datasets and runtimes**:

- this repository owns the full TSA 48 benchmark, the calibrated THLB, the AAC
  target, and the part accounting;
- `femic-northisland-instance` owns the NICC + K3Z student model and its
  planning targets;
- the full model carries a `part` flag (`nicc` or `outside`) and a `k3z` flag,
  so the NICC overlap can be isolated without rebuilding a separate inventory.

They can be used together — the full-model NICC share is the reference for the
NICC targets — or separately, when a project only needs one scale. Neither
repository requires the other to build or run.

## Status

The calibrated full-model benchmark is built and served. The `aac_benchmark`
run meets all ten decade targets at the published `1,248,100 m3/yr` AAC. The
NICC share is computed from the same run and is the reference for the NICC
model. Accepted TIPSY curves and reviewed policy targets remain before release.

## AOI

The tracked full TSA 48 boundary is `data/source/aoi/tsa48_full.gpkg`
(EPSG:3005, 2,441,931.03 ha gross). The NICC intersection is
`data/source/aoi/tsa48_nicc.gpkg` (1,083,012.84 ha gross), and the K3Z tenure
is `data/source/aoi/k3z_tenure.gpkg`.

## Model

| Quantity | Full TSA 48 | NICC part | Outside part |
| --- | ---: | ---: | ---: |
| Blocks | 110,728 | 51,292 | 59,436 |
| Block area | 1,092,831.62 ha | 442,591.61 ha | 650,240.01 ha |
| Managed area (THLB) | 177,505.00 ha | 38,960.29 ha | 138,544.71 ha |

The calibrated proportion scales each stand's `thlb_raw / 100` by
`1.4461532388060396`, capped at `1.0`; the capped area is exactly
`177,505.0 ha`. K3Z touches 253 blocks and 2,093.48 ha.

The calibrated model tree is `runtime/tsa48_full_calibrated/`:

- `matrix/` — full model;
- `matrix_nicc/`, `matrix_outside/` — filtered part datasets;
- `parts/block_parts.csv` — `part` and `k3z` flags;
- `schedules/`, `runs/` — part schedules and simulations;
- `evidence/` — calibration, part accounting and TSR benchmark reports;
- `fragments.geojson` — exact UI geometry;
- `land_base.geojson` — non-forest underlay.

## Benchmark

`config/targets.tsa48_full.yaml` carries ten per-decade targets with a
`12,480,000–12,481,000 m3` band around the `1,248,100 m3/yr` AAC. The
seed-greedy `aac_benchmark` schedule meets all ten decades, with 9,335 blocks
and 17,574 treatment events.

The NICC part contributes:

- first-decade harvest **2,145,437 m3**;
- **17.19%** of the full-model first-decade harvest;
- **≈214,544 m3/yr** scaled to the published AAC, the current NICC reference.

The benchmark is volume-only: spatial adjacency, opening-size and green-up
constraints are not yet applied. See
`notes/reference/two-model-tsa48-nicc.md` and `notes/reference/related-instances.md` for the decisions and evidence.

## Web UI

```bash
./serve_tsa48_calibrated.sh
```

The calibrated service listens on `http://127.0.0.1:8016/`. `PORT=...`
overrides the default. The script passes `--crs EPSG:3005`, `--allow-runs`,
`--allow-agent`, the exact block geometry, and the AOI land-base underlay; the
agent's working directory is the instance root.

The uncalibrated full model is served by `./serve_tsa48_full.sh` on port 8015
when that model tree is present.

The service binds loopback only. ws4 has no authentication; do not expose it
without a trusted proxy. MapLibre projects the EPSG:3005 geometry to WGS84 in
the browser.

## Build

The calibrated full model is rebuilt by:

```bash
MODEL_DIR=runtime/tsa48_full_calibrated \
PATCHWORKS_OUT=output/patchworks_tsa48_full_calibrated \
CALIBRATE_THLB=1 \
scripts/build_full_tsa48_model.sh
```

The script exports the FEMIC inventory, compiles and validates the ws4 matrix,
flags NICC/outside/K3Z parts, builds part datasets and schedules, simulates and
reports each part, and generates the exact UI and land-base geometry. The
Patchworks export is an interchange package only.

The upstream data root must contain the public BC TSA, VRI and VDYP input
surfaces. VDYP7 runs under Wine on Linux; the host needs `wine` and `wine32`.
The first lane uses the VDYP-transform managed curve mode, so it does not
require BatchTIPSY. Replace that lane with accepted TIPSY output before
release.

## Live benchmark watcher

```bash
scripts/watch_aac_benchmark.sh
```

This attaches `ws4 watch` to the full model in live mode. It is observational:
it does not persist a run. `SEED_GREEDY=0` starts from an empty schedule.

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Agent operating contract and project-specific rules |
| `ROADMAP.md` | Phases, tasks, and GitHub issue map |
| `CHANGE_LOG.md` | Dated narrative of changes |
| `config/` | FEMIC run profile, TSA targets, TIPSY scaffold, Patchworks export config |
| `data/source/aoi/` | Tracked public AOI, NICC and K3Z boundaries |
| `scripts/` | Build, calibration, part accounting, topology, UI and watcher scripts |
| `docs/` | Sphinx site and RTFM surface |
| `notes/` | AOI decisions, ADRs, reference notes and reports |
| `tests/` | Unit and contract tests |

## Public-data boundary

This repository is public. Do not add raw MKRF cost or revenue spreadsheets,
private tenure data, credentials, or machine-specific paths. The public model
uses published BC data and public cost/price bases. The detailed financial
overlay lives in a separate private repository linked as a submodule; it is not
required to build or run the public model.

## License

MIT. See `LICENSE`.
