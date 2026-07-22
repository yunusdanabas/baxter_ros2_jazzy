# Getting Started: Simulation

This is the default 15-minute path for a clean ROS 2 Jazzy sim workspace. It ends at a measured, reversible `sim_tiny_trajectory` and does not require hardware, ROS 1, `baxter_bridge`, or Zenoh.

## Devcontainer Path

1. Open the repo in the devcontainer.
2. The post-create command imports `repos/baxter_core.repos` if needed, runs `rosdep`, and builds with the default sim command.
3. In a devcontainer terminal, source the workspace:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
```

4. Run the sim smoke in two terminals.

Terminal 1:

```bash
ros2 launch baxter_gz_sim sim.launch.py headless:=true
```

Terminal 2:

```bash
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Expected result: both arms report outbound and return errors at or below `0.02 rad`.

## Native Ubuntu 24.04 Path

Install the sim/MoveIt packages:

```bash
sudo apt-get update
sudo apt-get install -y \
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
  ros-jazzy-xacro
sudo rosdep init 2>/dev/null || true
rosdep update --rosdistro jazzy
```

Build from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p src
vcs import src < repos/baxter_core.repos
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Choose an unused domain and partition rather than copying `42` when other ROS or Gazebo sessions may be running. If a previous build used another workspace underlay, remove this workspace's generated `build/`, `install/`, and `log/` directories and rebuild from a shell that sources only `/opt/ros/jazzy`.

If `src/baxter_common_ros2` already exists, verify the required pin instead of importing over it:

```bash
git -C src/baxter_common_ros2 rev-parse HEAD
```

Expected SHA: `678bfabea8c895b4134951a6c076217a90b9e0e6`.

## Smoke Test

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim.launch.py headless:=true
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 control list_controllers
ros2 topic echo /joint_states --once
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Expected controllers:

```text
joint_state_broadcaster active
left_arm_controller active
right_arm_controller active
```

Expected trajectory result includes measured outbound and return checks for both arms:

```text
left_arm_controller ... outbound verified: max_error=... rad
left_arm_controller ... return verified: max_error=... rad
right_arm_controller ... outbound verified: max_error=... rad
right_arm_controller ... return verified: max_error=... rad
Reversible trajectories verified for both arms
```

## What This Does Not Install

The default path does not build `baxter_bridge`, install ROS 1 libraries, configure a robot hostname, enable real hardware, or add Zenoh fallback packages.
