#!/bin/bash
# Baxter hardware session environment setup.
# Source this:  source scripts/baxter_env.sh

export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LC_NUMERIC=C

# An active conda/mamba env puts its own python3 first in PATH, but rclpy's C
# extension is built for the system python3.12 — so `python3 scripts/py_bridge.py`
# dies with "No module named 'rclpy._rclpy_pybind11'". Drop the conda install
# from PATH for this session; nothing in the hardware path needs it.
if [ -n "${CONDA_PREFIX}" ] && [ -n "${CONDA_EXE}" ]; then
    _conda_root="$(dirname "$(dirname "${CONDA_EXE}")")"
    PATH="$(echo "${PATH}" | tr ':' '\n' | grep -vF "${_conda_root}/" | paste -sd:)"
    export PATH
    echo "NOTE: dropped ${_conda_root} from PATH (rclpy needs the system python3)"
    unset _conda_root
fi

# Robot. Address by mDNS hostname (from the robot's serial) — its DHCP lease
# moves, so a hardcoded IP goes stale. Override BAXTER_HOST to use another.
export BAXTER_HOST="${BAXTER_HOST:-011412P0024.local}"
BAXTER_IP="$(getent hosts "${BAXTER_HOST}" 2>/dev/null | awk '{print $1}' | head -1)"
export BAXTER_IP="${BAXTER_IP:-${BAXTER_HOST}}"
export ROS_MASTER_URI="http://${BAXTER_IP}:11311"

# Laptop IP the ROBOT can call back on. Must be derived from the route to the
# robot: this host has several interfaces (wifi + a stale static on another
# subnet), and picking the wrong one leaves the robot unable to reach us.
export ROS_IP="${ROS_IP:-$(ip route get "${BAXTER_IP}" 2>/dev/null | grep -oP 'src \K\S+')}"

# ROS 2 Jazzy + workspace
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$(dirname "${BASH_SOURCE[0]}")/../install/setup.bash" 2>/dev/null || true

echo "=== Baxter Hardware Session ==="
echo "BAXTER_HOST:     ${BAXTER_HOST}"
echo "BAXTER_IP:       ${BAXTER_IP}"
echo "ROS_MASTER_URI:  ${ROS_MASTER_URI}"
echo "ROS_IP:          ${ROS_IP}"
echo "RMW:             ${RMW_IMPLEMENTATION}"
echo "LC_NUMERIC:      ${LC_NUMERIC}"
echo ""
echo "Terminal 1: python3 scripts/py_bridge.py"
echo "Terminal 2: ros2 run baxter_hardware_bridge baxter_safety_check"
echo "Terminal 3: ros2 launch baxter_hardware_bridge hardware_bringup.launch.py"
