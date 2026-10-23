#!/usr/bin/env python3
"""Check the materialized public data root and write a provenance manifest.

FEMIC reads BC VRI, VDYP input, TSA, and SiteProd sources from
``FEMIC_EXTERNAL_DATA_ROOT``. The canonical tree is ``femic-public-data/data``.
This script verifies that every required path is present and materialized (not a
broken annex symlink), records a key-table checksum for each file geodatabase,
and writes a tracked manifest without machine-specific paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

REQUIRED_PATHS: tuple[str, ...] = (
    "bc/tsa/FADM_TSA.gdb",
    "bc/siteprod/Site_Prod_BC.gdb",
    "bc/vri/2025/VEG_COMP_LYR_R1_POLY_2025.gdb",
    "bc/vri/2025/VEG_COMP_VDYP7_INPUT_POLY_AND_LAYER_2025.gdb",
)
KEY_TABLE = "a00000001.gdbtable"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_public_data(root: Path, *, hashes: bool = True) -> dict[str, object]:
    """Validate a materialized public data root and return a manifest.

    Parameters
    ----------
    root : Path
        Directory that contains ``bc/tsa``, ``bc/vri``, and ``bc/siteprod``.
    hashes : bool
        When ``True``, hash each file geodatabase's key table.

    Returns
    -------
    dict
        A JSON-ready manifest with the required paths, sizes, and checksums.

    Raises
    ------
    FileNotFoundError
        When a required path or its key table is missing.
    OSError
        When a path is a broken symlink or cannot be read.
    """
    root = Path(root)
    entries: list[dict[str, object]] = []
    for relative in REQUIRED_PATHS:
        path = root / relative
        if not path.exists():
            raise FileNotFoundError(f"missing public data path: {relative}")
        key_table = path / KEY_TABLE
        if not key_table.is_file():
            raise FileNotFoundError(f"missing key table: {relative}/{KEY_TABLE}")
        file_count = sum(1 for _ in path.iterdir())
        entries.append(
            {
                "path": relative,
                "key_table": KEY_TABLE,
                "key_table_bytes": key_table.stat().st_size,
                "key_table_sha256": _sha256(key_table) if hashes else None,
                "entry_count": file_count,
            }
        )
    return {
        "root": "${FEMIC_EXTERNAL_DATA_ROOT}",
        "required_paths": list(REQUIRED_PATHS),
        "entries": entries,
    }


def main() -> None:
    """Check the data root and write the tracked manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("FEMIC_EXTERNAL_DATA_ROOT", "external/femic-public-data/data")),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/source/public_data_manifest.json"),
    )
    parser.add_argument("--no-hashes", action="store_true")
    args = parser.parse_args()

    manifest = check_public_data(args.root, hashes=not args.no_hashes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
