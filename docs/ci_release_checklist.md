# CI And Release Checklist

This checklist reflects the current sim-first baseline. It is not a hardware release checklist.

## Default CI Checks

Default CI is hardware-free and should keep doing these checks:

```bash
source /opt/ros/jazzy/setup.bash
test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Run release evidence from `bash --noprofile --norc` or an equivalent clean shell. Before rebuilding after a workspace/underlay change, remove generated `build/`, `install/`, and `log/`. Generated setup files must not reference a deleted workspace.

Then run:

| Check | Current status |
|---|---:|
| Python compile/import for local launch/example files | passed |
| Xacro expansion of `baxter_gz_control.urdf.xacro` | passed |
| `check_urdf` on generated model | passed |
| Static fixed-world, 17-state/14-command, and neutral-state checks | passed |
| Finite controller limit/tolerance checks | passed |
| Static SRDF ACM and MoveIt/OMPL/RViz config checks | passed |

The CI path must not install ROS 1 or robot-network dependencies, start the
experimental hardware bridge, connect to a robot, or install Zenoh.

## Manual Sim Smoke

Run from the repository root after building:

Choose one unused pair for the entire test:

```bash
export ROS2CLI_NO_DAEMON=1
```

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 control list_controllers
ros2 topic echo /joint_states --once
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Pass criteria:

```text
all three controllers active
17 independent joints with advancing stamps
fixed world -> base at z=0.92418
RobotModel and TF status OK
outbound and return max_error <= 0.02 rad for each arm
motion visible in Gazebo and RViz
```

Run cancellation separately with `ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true -p cancel_after_sec:=1.0`. Require accepted cancellation, held position, bounded exit, and no traceback.

## Manual MoveIt Sim Smoke

Run from the repository root after building:

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
export ROS2CLI_NO_DAEMON=1
ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 action list
ros2 run baxter_examples moveit_left_tiny
ros2 run baxter_examples moveit_tiny --ros-args -p group:=right_arm
ros2 run baxter_examples moveit_tiny --ros-args -p group:=both_arms
ros2 run baxter_examples moveit_pose --ros-args -p group:=left_arm -p delta_z:=0.05
ros2 run baxter_examples ik_service_client --ros-args -p limb:=left
ros2 run baxter_examples ik_service_client --ros-args -p limb:=left -p x:=9.0
```

Pass criteria:

```text
/move_action
move_group logs "You can start planning now!" with pipeline ompl
no missing head/source-finger state warning
left, right, and both-arm outbound/return max_error <= 0.02 rad
moveit_pose reaches both absolute and delta targets
ik_service_client solves left/right and exits non-zero on an unreachable pose
motion visible in Gazebo
robot visible in RViz via the RobotModel/TF displays
OMPL and RRTConnectkConfigDefault available in MotionPlanning
```

The MotionPlanning panel must load: no `Exception caught while processing action 'loadRobotModel'`, a populated planner dropdown instead of `NO PLANNING LIBRARY LOADED`, a 6-DOF interactive marker on each gripper, and no `No robot state or robot model loaded`. A comma-decimal `LC_NUMERIC` is the known trigger for all four at once; see `known_issues.md`.

Run `moveit_tiny` once with `-p cancel_after_sec:=1.0`. Then send one Ctrl+C to the owning launch, wait, and require no Gazebo, bridge, controller, robot-state-publisher, MoveIt, or RViz process remains. Gazebo `-2` is expected after SIGINT; a hang, leftover process, or `move_group` crash fails the gate.

Retain the launch logs, numeric outputs, environment values, and before/target/return screenshots or video before citing them as evidence.

## Hardware Gates Not Yet Run

| Gate | Status |
|---|---:|
| I10 hardware bridge non-motion | blocked |
| I11 hardware action shims and safety tools | blocked |
| I12 supervised hardware motion | blocked |

Do not claim hardware support or supervised motion in release notes until those gates pass and their logs contain evidence.

## Release Hardening Checks

Before tagging a sim-first release, verify these files exist and use the same profile labels as this checklist:

| File | Required status |
|---|---:|
| `LICENSE` | BSD-3-Clause for local project code |
| `CONTRIBUTING.md` | Present |
| `SUPPORT.md` | Present |
| `SECURITY.md` | Present |
| `CHANGELOG.md` | Present |
| `.github/ISSUE_TEMPLATE/` | Sim bug, hardware bridge bug, docs, safety concern, pin update, feature request |
| `.github/pull_request_template.md` | Present |
| `docs/simulation_baseline.md` | Present |
| `docs/maintainer_handoff.md` | Present |

## Release No-Go Conditions

Do not release the sim-first profile if any of these are true:

| Condition | Current status |
|---|---:|
| Default `.repos` imports anything besides the pinned ECN source | no-go if true |
| Default build omits `--packages-skip baxter_bridge` | no-go if true |
| Docs imply hardware support or supervised hardware motion | no-go if true |
| Beginner docs teach raw safety-topic publishing | no-go if true |
| Root project or local package licenses still contain `TODO` | no-go if true |
