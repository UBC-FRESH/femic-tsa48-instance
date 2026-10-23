# Full TSA 48 benchmark and web UI

The full-model benchmark is the ten-decade AAC run in
`runtime/tsa48_full_calibrated/runs/aac_benchmark`. It is volume-only: spatial
opening and green-up constraints are not yet applied.

## Benchmark

- Dataset: `runtime/tsa48_full_calibrated/matrix`
- Schedule: 9,335 blocks, 17,574 treatment events
- Horizon: 100 years, ten accounting periods of 10 years
- Target: `12,480,000-12,481,000 m3` per decade around the 1,248,100 m3/yr AAC
- Result: all 10 decade targets met

The NICC part contributes 2,145,437 m3 in the first decade, 17.19% of the
full-model first-decade harvest. Scaled to the published AAC, the current NICC
reference is **≈214,544 m3/yr**. See
`notes/reference/two-model-tsa48-nicc.md`.

## Web UI

```bash
./serve_tsa48_calibrated.sh
```

The calibrated launcher binds `127.0.0.1:8016`, passes `--crs EPSG:3005`, the
exact block geometry, the AOI land-base underlay, `--allow-runs`, and
`--allow-agent`, with the agent working directory at the instance root.

Verification:

- `/health` returns `{"status":"ok"}`.
- The run list contains `aac_benchmark (search)` and the part runs.
- The map renders 110,728 exact block polygons.
- The Targets tab shows the ten AAC periods with min/max/achieved/status.
- The land-base underlay keeps non-forest gaps from reading as missing geometry.
- The map API uses gzip; the exact full-model geometry is large on purpose.
- If WebGL is unavailable, the **SVG (fallback)** map engine renders the same blocks.

The uncalibrated full model is served by `./serve_tsa48_full.sh` on port 8015
when that model tree exists.

## Related dataset

The NICC + K3Z model is a separate instance in
`UBC-FRESH/femic-northisland-instance`. It is not required to run this model.
