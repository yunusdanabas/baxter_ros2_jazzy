#!/bin/bash
# Baxter hardware session environment setup.
# Source this:  source scripts/baxter_env.sh

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# Robot
export BAXTER_IP="${BAXTER_IP:-192.168.1.224}"
export ROS_MASTER_URI="http://${BAXTER_IP}:11311"

# Laptop IP on the robot network
export ROS_IP="${ROS_IP:-$(hostname -I | awk '{print $1}')}"

# ROS 2 Jazzy + workspace
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$(dirname "${BASH_SOURCE[0]}")/../install/setup.bash" 2>/dev/null || true

echo "=== Baxter Hardware Session ==="
echo "BAXTER_IP:       ${BAXTER_IP}"
echo "ROS_MASTER_URI:  ${ROS_MASTER_URI}"
echo "ROS_IP:          ${ROS_IP}"
echo "ROS_DOMAIN_ID:   ${ROS_DOMAIN_ID}"
echo "RMW:             ${RMW_IMPLEMENTATION}"
echo ""
echo "Terminal 1: python3 scripts/py_bridge.py"
echo "Terminal 2: ros2 run baxter_hardware_bridge baxter_safety_check"
echo "Terminal 3: ros2 launch baxter_hardware_bridge hardware_bringup.launch.py"
