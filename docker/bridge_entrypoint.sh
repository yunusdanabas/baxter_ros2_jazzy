#!/bin/bash
set -e

# Source both ROS 1 and ROS 2
source /opt/ros/noetic/setup.bash
source /opt/ros/foxy/setup.bash
source /ws/install/setup.bash

export ROS_DISTRO=foxy

# Use FastDDS for cross-distro DDS compatibility with Jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# Robot connection must be supplied explicitly at runtime.
: "${ROS_MASTER_URI:?Set ROS_MASTER_URI to the Baxter ROS 1 master URI}"
: "${ROS_IP:?Set ROS_IP to the bridge host address on the robot network}"
export ROS_MASTER_URI ROS_IP
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

echo "=== Baxter Bridge Container ==="
echo "ROS_MASTER_URI: ${ROS_MASTER_URI}"
echo "ROS_IP: ${ROS_IP}"
echo "ROS_DOMAIN_ID: ${ROS_DOMAIN_ID}"
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
