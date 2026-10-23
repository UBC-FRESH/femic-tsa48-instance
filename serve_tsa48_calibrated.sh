#!/usr/bin/env bash
# Serve the calibrated full TSA 48 ws4 model on loopback.
set -euo pipefail

INSTANCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8016}"
MODEL_DIR="${MODEL_DIR:-$INSTANCE_ROOT/runtime/tsa48_full_calibrated}"
DATASET="${DATASET:-$MODEL_DIR/matrix}"
RUNS="${RUNS:-$MODEL_DIR/runs}"
GEOMETRY="${GEOMETRY:-$MODEL_DIR/fragments.geojson}"
LAND_BASE="${LAND_BASE:-$MODEL_DIR/land_base.geojson}"
TARGETS="${TARGETS:-$INSTANCE_ROOT/config/targets.tsa48_full.yaml}"

cd "$INSTANCE_ROOT"
exec python -m ws4.cli serve \
  --dataset "$DATASET" \
  --runs "$RUNS" \
  --geometry "$GEOMETRY" \
  --land-base "$LAND_BASE" \
  --targets "$TARGETS" \
  --crs EPSG:3005 \
  --allow-runs \
  --allow-agent \
  --agent-cwd "$INSTANCE_ROOT" \
  --host 127.0.0.1 \
  --port "$PORT"
