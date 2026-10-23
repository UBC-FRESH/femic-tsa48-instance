TSA 48 AOI
==========

The model AOI is the full North Island Timber Supply Area, TSA 48. The tracked
boundary is ``data/source/aoi/tsa48_full.gpkg`` (EPSG:3005, layer
``tsa48_full``, 2,441,931.03 ha gross).

The full TSA is the benchmark boundary because the published AAC and THLB are
TSA-wide. The NICC overlap and K3Z tenure are block-level overlays, not separate
build boundaries.

Overlays
--------

| Layer | Path | Use |
| --- | --- | --- |
| NICC district | ``data/source/aoi/nicc_district.gpkg`` | ``part = nicc`` flag |
| NICC intersection | ``data/source/aoi/tsa48_nicc.gpkg`` | reviewed overlap geometry |
| K3Z tenure | ``data/source/aoi/k3z_tenure.gpkg`` | ``k3z`` flag |

``scripts/flag_parts.py`` joins those overlays to the compiled block parts. The
result is ``runtime/tsa48_full_calibrated/parts/block_parts.csv``.

Related instance
----------------

The NICC + K3Z model lives in
`UBC-FRESH/femic-northisland-instance <https://github.com/UBC-FRESH/femic-northisland-instance>`_.
The two datasets are deliberately related but independent. This repository
answers the full-TSA question; the NICC repository answers the district-scale
question. The full model's ``part = nicc`` accounting is the bridge, not a
runtime dependency.

Source notes
------------

The 2020 North Island TSA Timber Supply Review data package supplies the
published THLB and AAC. The 2024 determination PDF is context. Neither is a
geometry input. See ``notes/reference/aoi.md`` for the review record.
