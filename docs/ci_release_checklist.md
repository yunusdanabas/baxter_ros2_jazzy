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

Then run:

| Check | Status in I08 |
|---|---:|
| Python compile/import for local launch/example files | passed |
| Xacro expansion of `baxter_gz_control.urdf.xacro` | passed |
| `check_urdf` on generated model | passed |
| Static SRDF group/state/world-joint checks | passed |
| Static MoveIt controller/OMPL config checks | passed |

The CI path must not install hardware bridge tooling, ROS 1 dependencies, robot-network dependencies, or Zenoh.

## Manual Sim Smoke

Run from the repository root after building:

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim.launch.py headless:=true
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 control list_controllers
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Pass criteria:

```text
joint_state_broadcaster active
left_arm_controller active
right_arm_controller active
/left_arm_controller/follow_joint_trajectory succeeded
/right_arm_controller/follow_joint_trajectory succeeded
Tiny trajectories completed for both arms
```

## Manual MoveIt Sim Smoke

Run from the repository root after building:

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=true
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 action list
ros2 run baxter_examples moveit_left_tiny
```

Pass criteria:

```text
/move_action
MoveIt left-arm plan+execute passed
```

Full Gazebo plus MoveIt runtime is manual/local smoke for now because I07 observed a possible `move_group` SIGINT teardown segfault after successful execution.

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
| `docs/release_notes_v0.1.0-sim.md` | Present |
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
