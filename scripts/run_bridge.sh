#!/bin/bash
# Run the pure-Python bridge to Baxter.
# Usage: scripts/run_bridge.sh [robot_host]
#
# Thin wrapper around what the runbook documents:
#   source scripts/baxter_env.sh && python3 scripts/py_bridge.py
# Everything (robot address, ROS_IP, RMW, domain) comes from baxter_env.sh so
# the bridge and the action shim cannot drift onto different settings.

set -e

[ -n "$1" ] && export BAXTER_HOST="$1"

# shellcheck source=scripts/baxter_env.sh
source "$(dirname "$0")/baxter_env.sh"

exec python3 "$(dirname "$0")/py_bridge.py"
