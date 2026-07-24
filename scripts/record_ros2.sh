#!/bin/bash
# ROS 2 side session recorder — the bridged/shim view of the same session.
# Pair it with record_ros1.sh: the same JointState appears in both bags, so
# offline you can diff receive times (one host, one clock) to get bridge latency,
# and the shim's own action feedback/status only exists on this side.
#
# Snapshots the git revision and the LIVE node parameters first, so a bag can
# always be matched to the exact shim tolerances that produced it.
#
# Usage:   source scripts/baxter_env.sh && bash scripts/record_ros2.sh
#          (Ctrl-C to stop)
# Env:     SESSION_DIR, MIN_FREE_GB
#
# Self-check (no robot needed) — with the mock stack running:
#   ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false
#   timeout -s INT 10 bash scripts/record_ros2.sh
#   ros2 bag info data/sessions/$(date +%F)/ros2/full_*
# Expect: /robot/joint_states, /robot/limb/*/joint_command and the action topics.
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SESSION="${SESSION_DIR:-data/sessions/$(date +%F)}/ros2"
mkdir -p "$SESSION"
SESSION="$(cd "$SESSION" && pwd)"
STAMP="$(date +%H%M%S)"

MIN_FREE_GB="${MIN_FREE_GB:-10}"
FREE_GB="$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc '0-9')"
if [ "$FREE_GB" -lt "$MIN_FREE_GB" ]; then
    echo "REFUSING: only ${FREE_GB} GB free on $SESSION (need ${MIN_FREE_GB})." >&2
    exit 1
fi

echo "=== ROS 2 snapshot -> $SESSION (stamp $STAMP) ==="
{ git rev-parse HEAD; git status --short; } > "$SESSION/git_${STAMP}.txt"
ros2 topic list > "$SESSION/topics_${STAMP}.txt"
# Live params: the shim tolerances actually in force for this recording.
for n in $(ros2 node list); do
    echo "# $n"
    ros2 param dump "$n" 2>/dev/null || echo "  (no parameters)"
done > "$SESSION/node_params_${STAMP}.yaml"

echo "=== Recording all ROS 2 topics — Ctrl-C to stop ==="
# --include-hidden-topics is not optional here: action feedback and status live
# under .../_action/... and are hidden, so plain `-a` records the joint commands
# but silently drops the shim's own view of how each goal progressed.
exec ros2 bag record -a --include-hidden-topics -o "$SESSION/full_${STAMP}" \
    --max-bag-size 1073741824 --compression-mode file --compression-format zstd
