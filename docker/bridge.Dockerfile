FROM ros:foxy-ros1-bridge-focal

# Foxy and Noetic on Focal provide an official base with both ROS 1 and ROS 2.
# DDS topics cross to the laptop's Jazzy via shared RMW (FastDDS).

ENV DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    git \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws

COPY repos/baxter_core.repos /ws/repos/baxter_core.repos
RUN mkdir -p /ws/src \
    && vcs import /ws/src < /ws/repos/baxter_core.repos \
    && cd /ws/src/baxter_common_ros2 \
    && git checkout 678bfabea8c895b4134951a6c076217a90b9e0e6

# rosdep for ROS 2 deps (ROS 1 already in the base image)
RUN . /opt/ros/foxy/setup.bash \
    && . /opt/ros/noetic/setup.bash \
    && rosdep install --from-paths /ws/src --ignore-src -r -y \
    || true

# Build all 5 packages INCLUDING baxter_bridge
# Swap: factory_2to1.cpp OOM-kills in 2GB Docker; swap prevents that.
# -j1: no parallel make, one translation unit at a time.
RUN fallocate -l 4G /swapfile && mkswap /swapfile && swapon /swapfile \
    && . /opt/ros/foxy/setup.bash \
    && . /opt/ros/noetic/setup.bash \
    && export ROS_DISTRO=foxy \
    && cd /ws && colcon build --symlink-install --parallel 1 --executor sequential \
    && rm -f /swapfile

COPY docker/bridge_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bridge"]
