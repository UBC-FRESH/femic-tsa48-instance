#!/usr/bin/env bash
# Watch the calibrated full TSA 48 AAC benchmark converge in the ws4 watcher.
#
# Usage:
#   scripts/watch_aac_benchmark.sh
#   ITERATIONS=5000 REFRESH=1 scripts/watch_aac_benchmark.sh
#   SEED_GREEDY=0 scripts/watch_aac_benchmark.sh
#   PLAIN=1 scripts/watch_aac_benchmark.sh
#
# The script uses the calibrated full TSA 48 dataset and the ten-decade AAC
# targets. By default it seeds from the target-driven greedy schedule, so the
# watcher starts from a near-AAC schedule and then shows the search's
# refinements. Set SEED_GREEDY=0 to start from an empty schedule instead.
set -euo pipefail

INSTANCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET="${DATASET:-$INSTANCE_ROOT/runtime/tsa48_full_calibrated/matrix}"
TARGETS="${TARGETS:-$INSTANCE_ROOT/config/targets.tsa48_full.yaml}"
ACCOUNT="${ACCOUNT:-product.Yield.managed.Total}"
PERIOD_WIDTH="${PERIOD_WIDTH:-10}"
YEARS="${YEARS:-100}"
ITERATIONS="${ITERATIONS:-2000}"
REFRESH="${REFRESH:-2}"
SEED="${SEED:-42}"
SEED_GREEDY="${SEED_GREEDY:-1}"
PLAIN="${PLAIN:-0}"

args=(
  watch
  --dataset "$DATASET"
  --targets "$TARGETS"
  --account "$ACCOUNT"
  --period-width "$PERIOD_WIDTH"
  --years "$YEARS"
  --iterations "$ITERATIONS"
  --refresh "$REFRESH"
  --seed "$SEED"
)

if [ "$SEED_GREEDY" = "1" ]; then
  args+=(--seed-greedy)
fi
if [ "$PLAIN" = "1" ]; then
  args+=(--plain)
fi

cd "$INSTANCE_ROOT"
exec python -m ws4.cli "${args[@]}"
