Web UI
======

The ws4 web UI serves the full TSA 48 compiled dataset and its runs. It is
read-only except for the optional run and agent controls. It binds loopback by
default and has no authentication.

Launch
------

The calibrated full model is served by:

.. code-block:: bash

   ./serve_tsa48_calibrated.sh

The script expands to:

.. code-block:: bash

   python -m ws4.cli serve \
     --dataset runtime/tsa48_full_calibrated/matrix \
     --runs runtime/tsa48_full_calibrated/runs \
     --geometry runtime/tsa48_full_calibrated/fragments.geojson \
     --land-base runtime/tsa48_full_calibrated/land_base.geojson \
     --targets config/targets.tsa48_full.yaml \
     --crs EPSG:3005 \
     --allow-runs \
     --allow-agent \
     --port 8016

``PORT=...`` overrides the default. The geometry is EPSG:3005; pass
``--crs EPSG:3005`` so MapLibre can project it to WGS84. The land base is the
AOI polygon drawn under the blocks, so non-forest gaps read as land rather than
as missing map data.

The block layer still renders if the OpenStreetMap basemap tiles are
unavailable. If MapLibre cannot create a WebGL context, switch **Map engine** to
**SVG (fallback)**.

The full map contains 110,728 block polygons. The UI geometry is exact
(``--simplify-m 0``), so the response is large but every source vertex is kept.
The land base adds about 1.4 MB.

Checks
------

- ``/health`` returns ``{"status":"ok"}``.
- The map shows the full TSA 48 AOI, not the NICC-only area.
- The run list contains ``aac_benchmark`` and the part runs.
- The target table shows ten decade targets and their realized values.
- The NICC/outside part flags are visible in block attributes and accounting.

Do not use ``--allow-remote`` on an untrusted network. Put the service behind a
trusted proxy if it must be reachable from another host.
