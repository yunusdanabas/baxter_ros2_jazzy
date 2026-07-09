FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    ca-certificates \
    git \
    python3-argcomplete \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    ros-jazzy-desktop \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-moveit \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros-gz \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-xacro \
  && rm -rf /var/lib/apt/lists/*

RUN rosdep init 2>/dev/null || true \
  && rosdep update --rosdistro jazzy

RUN printf '%s\n' \
    'source /opt/ros/jazzy/setup.bash' \
    >/etc/profile.d/baxter_ros2_jazzy.sh
