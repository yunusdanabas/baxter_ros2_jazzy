#!/bin/bash
# Run the pure-Python bridge to Baxter.
# Usage: scripts/run_bridge.sh [robot_ip]

set -e

ROBOT_IP="${1:-192.168.1.224}"
LOCAL_IP="${2:-$(hostname -I | awk '{print $1}')}"

source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$(dirname "$0")/../install/setup.bash" 2>/dev/null || true

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "Starting Python bridge to Baxter at ${ROBOT_IP} (local: ${LOCAL_IP})"
exec python3 "$(dirname "$0")/py_bridge.py" --master "http://${ROBOT_IP}:11311" --ip "${LOCAL_IP}"
