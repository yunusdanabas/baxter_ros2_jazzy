#!/bin/bash
set -e

# Source both ROS 1 and ROS 2
source /opt/ros/noetic/setup.bash
source /opt/ros/foxy/setup.bash
source /ws/install/setup.bash

export ROS_DISTRO=foxy

# Use FastDDS for cross-distro DDS compatibility with Jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# Robot connection — required at runtime (DHCP leases move; no lab IP default).
if [ -z "${ROS_MASTER_URI:-}" ]; then
    echo "ERROR: set ROS_MASTER_URI (e.g. export ROS_MASTER_URI=http://<robot-ip>:11311)" >&2
    exit 1
fi
export ROS_MASTER_URI
export ROS_IP="${ROS_IP:-$(hostname -I | awk '{print $1}')}"
# No ROS_DOMAIN_ID: the container must share the host's default domain or the
# action shim on the laptop never sees the bridged topics.

echo "=== Baxter Bridge Container ==="
echo "ROS_MASTER_URI: ${ROS_MASTER_URI}"
echo "ROS_IP: ${ROS_IP}"
echo "RMW: ${RMW_IMPLEMENTATION}"
echo

case "${1:-bridge}" in
  bridge)
    echo "Starting baxter_bridge..."
    ros2 run baxter_bridge bridge --ros-args -p use_baxter_description:=false
    ;;
  static)
    echo "Starting baxter_bridge (static mode)..."
    ros2 run baxter_bridge bridge -s --ros-args -p use_baxter_description:=false
    ;;
  shell)
    exec bash
    ;;
  *)
    exec "$@"
    ;;
esac
