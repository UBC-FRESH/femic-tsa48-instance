Model Build
===========

The calibrated full TSA 48 model is built by
``scripts/build_full_tsa48_model.sh``. The script records each command and
artifact path; the Patchworks XML/fragments pair is an interchange input to
``ws4 build``, not the runtime lane.

Chain
-----

.. code-block:: text

   femic export patchworks
     -> ws4 build
     -> ws4 validate
     -> flag_parts (NICC / outside / K3Z)
     -> build_part_schedules
     -> build_part_datasets
     -> ws4 simulate + report per part
     -> prepare_ws4_ui (exact block geometry)
     -> prepare_land_base (non-forest underlay)

FEMIC compiles the public inventory and yield curves and writes the model-input
bundle. The export reads the calibrated checkpoint so each stand carries the
proportional THLB signal. ws4 compiles the full matrix and runs the benchmark
and part accounting.

The calibrated model has 110,728 blocks, 1,092,831.62 ha of block area, and
177,505.00 ha of managed area. NICC is 51,292 blocks and 38,960.29 managed ha;
outside is 59,436 blocks and 138,544.71 managed ha. K3Z touches 253 blocks and
2,093.48 ha.

Commands
--------

.. code-block:: bash

   MODEL_DIR=runtime/tsa48_full_calibrated \
   PATCHWORKS_OUT=output/patchworks_tsa48_full_calibrated \
   CALIBRATE_THLB=1 \
   scripts/build_full_tsa48_model.sh

Set ``FEMIC_EXTERNAL_DATA_ROOT`` to the public BC data root if the FEMIC
preflight needs it. The generated matrix, runs, evidence, and UI geometry are
written under ``runtime/tsa48_full_calibrated/`` and are ignored by Git.

The AAC benchmark is launched from the web UI or by the live watcher:

.. code-block:: bash

   scripts/watch_aac_benchmark.sh

Runtime boundary
----------------

VDYP7 is a Windows executable. On Linux it runs under Wine, including the
32-bit loader. The first lane sets ``vdyp_sampling_mode: auto`` because the
larger ``all`` batches exceeded the short VDYP console timeout in the first run.
Auto sampling fits from fewer stands, so it is a provisional workaround; raise
the timeout and rerun in ``all`` mode before release.

The first lane also sets ``managed_curve_mode: vdyp_transform`` and therefore
does not need BatchTIPSY. That transform is a provisional managed curve lane,
not accepted TIPSY yield curves. Replace it before release.

The THLB calibration is a proportional rescale, not the reviewed 2020 TSR
netdown. The benchmark assumes the calibrated 177,505 ha managed area.
