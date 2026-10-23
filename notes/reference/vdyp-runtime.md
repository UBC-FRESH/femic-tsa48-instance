# VDYP runtime boundary

The public build uses the bundled VDYP7 console executable:

```text
VDYP7/VDYP7/VDYP7Console.exe
```

It is a 32-bit Windows executable. On Linux, FEMIC runs it through Wine. The host
needs both `wine64` and `wine32` (the i386 architecture).

## Batch timeout

FEMIC gives each VDYP console invocation a short batch timeout. In the first
North Island run, the `all` sampling mode sent large strata batches (3,791 to
9,216 features) and the console exceeded the timeout. The run still exited 0,
but CWH_HW, CWH_FD, and CWH_CW-H had no curves in `vdyp_results`.

Evidence:

```text
runtime/logs/vdyp_runs-tsanorthisland-northisland_20261021.jsonl
status=timeout, timeout_sec=30, feature_count=3791
status=timeout, timeout_sec=30, feature_count=5897
status=timeout, timeout_sec=30, feature_count=9216
status=ok, duration_sec=22.8, feature_count=1557
```

## First-lane workaround

The first lane sets `vdyp_sampling_mode: auto` and
`vdyp_two_pass_rebin: false`. With two-pass rebin enabled, FEMIC forces the first
VDYP pass back to `all`; disabling it keeps the auto sampler, which caps each
batch at the configured sample size. The trade-off is that natural curves are
fitted from the sampled stands, not every stand in the stratum.

The successful first run covered 12 AUs: CWH_HW, CWH_CW, CWH_YC, and CWH_FD,
each at L/M/H. It wrote 51,289 fragments and 49 curves.

This is a provisional workaround. Before release, either:

- raise the FEMIC VDYP batch timeout and rerun in `all` mode, or
- provide accepted VDYP curve output with a recorded provenance manifest.

## Managed-curve boundary

`managed_curve_mode: vdyp_transform` applies a scale/truncation transform to the
natural curves. It is not an accepted TIPSY yield curve. Replace it with a
BatchTIPSY handoff (input CSV, output CSV, treated curves, and diagnostics)
before this instance is called production-ready.
