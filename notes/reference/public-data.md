# Public data root

FEMIC reads its public inputs from `FEMIC_EXTERNAL_DATA_ROOT`. The canonical tree
is the `data` directory of `UBC-FRESH/femic-public-data`. Large layers are
annex-backed; a pointer symlink is not a usable input until `datalad get` or
`git annex get` materializes it.

## Required paths

| Relative path | Use |
| --- | --- |
| `bc/tsa/FADM_TSA.gdb` | TSA boundary context and the TSA 48 source |
| `bc/siteprod/Site_Prod_BC.gdb` | Site productivity lookup |
| `bc/vri/2025/VEG_COMP_LYR_R1_POLY_2025.gdb` | Current VRI layer |
| `bc/vri/2025/VEG_COMP_VDYP7_INPUT_POLY_AND_LAYER_2025.gdb` | VDYP input layer and polygon |

## Check command

```bash
export FEMIC_EXTERNAL_DATA_ROOT=/path/to/femic-public-data/data
python scripts/check_public_data.py \
  --out data/source/public_data_manifest.json
```

The manifest records the key-table SHA-256 and entry count for each
geodatabase. It stores the root as `${FEMIC_EXTERNAL_DATA_ROOT}`, so it is safe
to commit and portable across machines.

## Materialization notes

- Use `git submodule update --init external/femic-public-data` from the parent
  FEMIC checkout.
- Enable the `arbutus-s3` remote and run `datalad get` for the VRI and SiteProd
  paths. The runbook in the parent FEMIC repository covers the auth order.
- A GDB directory that contains only annex pointer symlinks is a blocker, not a
  warning. Verify `a00000001.gdbtable` resolves to a real file.
